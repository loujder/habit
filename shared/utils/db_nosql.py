from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from sqlalchemy.future import select
from sqlalchemy import update
from shared.models.user import User1
import redis.asyncio as redis
from shared.utils.config import settings

from shared.utils.db_sql import engine, async_session
import json
import time

rdb = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASSWORD)





class UserCache:
    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        mongo_db_name: str = "habit_quest_cache",
        mongo_collection: str = "user_stats"
    ):
        self.mongo_db = mongo_client[mongo_db_name]
        self.collection = self.mongo_db[mongo_collection]
        self.engine = engine
        self.async_session = async_session
    
    async def initialize(self):
        await self.clear_cache()
        await self.collection.create_index(
            "expire_at",
            expireAfterSeconds=0
        )
        await self.collection.create_index("user_id", unique=True)
    
    async def get_stats(self, user_id: int) -> dict:
        """Получение статистики пользователя с кешированием"""
        cached = await self.collection.find_one({"user_id": user_id})
        now = datetime.utcnow()
        
        if cached and cached.get('expire_at', now) > now:
            return cached['data']
        
        stats = await self._fetch_from_db(user_id)
        await self._save_to_cache(user_id, stats)
        return stats
    
    async def _fetch_from_db(self, user_id: int) -> dict:
        """Получение данных из основной базы (SQLAlchemy)"""
        async with self.async_session() as session:
            result = await session.execute(select(User1).filter(User1.chat_id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User1(
                    id=user_id,
                    stars=0,
                    awards=0,
                    streak=0,
                    created_at=datetime.utcnow(),
                    status='user',
                    premium_expiry=None,
                    target='Здесь пока пусто...',
                    notification=True
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            
            return {
                "stars": user.stars,
                "awards": user.awards,
                "streak": user.streak,
                "created_at": user.created_at,
                'status': user.status,
                'premium_expiry': user.premium_expiry,
                'target': user.target,
                'notification': user.notification
            }
    
    async def _save_to_cache(self, user_id: int, stats: dict):
        """Сохранение данных в MongoDB кеш"""
        expire_at = datetime.utcnow() + timedelta(minutes=15)
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "data": stats,
                "expire_at": expire_at
            }},
            upsert=True
        )
    
    async def update_stats(
        self,
        user_id: int,
        stars_delta: int = 0,
        awards_delta: int = 0,
        streak_delta: int = 0,
        target: str = None,
        status: str = None,
        premium_expiry: datetime = None,
        notification: bool = None
    ):
        """Обновление статистики в обеих базах"""
        await self._update_main_db(
            user_id,
            stars_delta,
            awards_delta,
            streak_delta,
            target,
            status,
            premium_expiry,
            notification
        )
        
        update_query = {"$set": {"last_update": datetime.utcnow()}}
        
        if stars_delta:
            update_query["$inc"] = {"data.stars": stars_delta}
        if awards_delta:
            update_query.setdefault("$inc", {})["data.awards"] = awards_delta
        if streak_delta:
            update_query.setdefault("$inc", {})["data.streak"] = streak_delta
        if target:
            update_query.setdefault("$set", {})["data.target"] = target
        if status:
            update_query.setdefault("$set", {})["data.status"] = status
        if premium_expiry is not None:
            update_query.setdefault("$set", {})["data.premium_expiry"] = premium_expiry
        if notification is not None:
            update_query.setdefault("$set", {})["data.notification"] = notification
        
        update_query["$set"]["expire_at"] = datetime.utcnow() + timedelta(minutes=15)
        
        await self.collection.update_one(
            {"user_id": user_id},
            update_query,
            upsert=True
        )
    
    async def _update_main_db(
        self,
        user_id: int,
        stars_delta: int,
        awards_delta: int,
        streak_delta: int,
        target: str,
        status: str,
        premium_expiry: datetime,
        notification: bool
    ):
        """Обновление основной базы данных"""
        async with self.async_session() as session:
            update_stmt = update(User1).where(User1.chat_id == user_id)
            
            if stars_delta:
                update_stmt = update_stmt.values(stars=User1.stars + stars_delta)
            if awards_delta:
                update_stmt = update_stmt.values(awards=User1.awards + awards_delta)
            if streak_delta:
                update_stmt = update_stmt.values(streak=User1.streak + streak_delta)
            if target:
                update_stmt = update_stmt.values(target=target)
            if status:
                update_stmt = update_stmt.values(status=status)
            if premium_expiry is not None:
                update_stmt = update_stmt.values(premium_expiry=premium_expiry)
            if notification is not None:
                update_stmt = update_stmt.values(notification=notification)
            
            update_stmt = update_stmt.values(last_active=datetime.utcnow())
            
            result = await session.execute(update_stmt)
            
            if result.rowcount == 0:
                user = User1(
                    id=user_id,
                    stars=stars_delta or 0,
                    awards=awards_delta or 0,
                    streak=streak_delta or 0,
                    target=target or 'Здесь пока пусто...',
                    status=status or 'user',
                    premium_expiry=premium_expiry,
                    notification=notification if notification is not None else True
                )
                session.add(user)
            
            await session.commit()
    
    async def set_premium(
        self,
        user_id: int,
        duration: timedelta
    ):
        """Установить премиум-статус на указанный срок"""
        expiry_date = datetime.utcnow() + duration
        await self.update_stats(
            user_id,
            status='premium',
            premium_expiry=expiry_date
        )
    
    async def get_status(self, user_id: int) -> str:
        """Получить текущий статус с автоматическим понижением по истечении срока"""
        stats = await self.get_stats(user_id)
        now = datetime.utcnow()
        
        # Проверяем истек ли премиум
        if (stats['status'] == 'premium' and 
            stats.get('premium_expiry') and 
            stats['premium_expiry'] < now):
            
            # Автоматическое понижение до user
            await self.update_stats(
                user_id,
                status='user',
                premium_expiry=None
            )
            return 'user'
        
        return stats['status']
    
    async def invalidate(self, user_id: int):
        """Сброс кеша пользователя"""
        await self.collection.delete_one({"user_id": user_id})
    
    async def clear_cache(self):
        """Удаление всего кеша пользователей"""
        await self.collection.delete_many({})
        print("Весь кеш пользователей успешно удален")
    
    async def close(self):
        try:
            await self.clear_cache()
            await self.engine.dispose()
            print("Соединения с БД закрыты")
        except Exception as e:
            print(f"Ошибка при закрытии: {e}")



class UserFriends:
    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        mongo_db_name: str = "habit_quest",
        mongo_collection: str = "user_friends"
    ):
        """
        Управление друзьями пользователей
        
        :param mongo_client: Инициализированный AsyncIOMotorClient
        :param mongo_db_name: Имя базы данных MongoDB
        :param mongo_collection: Имя коллекции для хранения друзей
        """
        self.mongo_db = mongo_client[mongo_db_name]
        self.collection = self.mongo_db[mongo_collection]
        
    async def initialize(self):
        """Создаем индексы при инициализации"""
        await self.collection.create_index("user_id")
        await self.collection.create_index("friend_id")
        await self.collection.create_index([("user_id", 1), ("friend_id", 1), ('username', 1)], unique=True)
    
    async def add_friend(self, user_id: int, friend: dict, user: dict):
        """Добавление друга"""
        await self.collection.update_one(
            {"user_id": int(user_id)},
            {"$addToSet": {"friends": friend}},
            upsert=True
        )
        await self.collection.update_one(
            {"user_id": int(friend[0])},
            {"$addToSet": {"friends": user}},
            upsert=True
        )
    
    async def remove_friend(self, user_id: int, friend_id: int):
        """Удаление друга"""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$pull": {"friends": friend_id}}
        )
        await self.collection.update_one(
            {"user_id": friend_id},
            {"$pull": {"friends": user_id}}
        )
    
    async def get_friends(self, user_id: int) -> list[int]:
        """Получение списка друзей"""
        document = await self.collection.find_one({"user_id": user_id})
        return document.get("friends", []) if document else []
    
    async def get_friends_details(self, user_id: int, user_cache: UserCache) -> list[dict]:
        """Получение детальной информации о друзьях"""
        friends_ids = await self.get_friends(user_id)
        friends_data = []
        
        for friend_id in friends_ids:
            stats = await user_cache.get_stats(friend_id[0])
            friends_data.append({
                "user_id": friend_id,
                "stars": stats.get("stars", 0),
                "awards": stats.get("awards", 0),
                "streak": stats.get("streak", 0),
                "status": stats.get("status", "user"),
                "target": stats.get("target", "Здесь пока пусто..."),
                "date": stats.get("created_at", None)
            })
        
        return friends_data
    
    async def are_friends(self, user_id: int, friend_id: int) -> bool:
        """Проверка, являются ли пользователи друзьями"""
        document = await self.collection.find_one({
            "user_id": user_id,
            "friends": {"$elemMatch": {"$elemMatch": {"$eq": friend_id}}}
        })
        return document is not None
    
    async def get_friend_requests(self, user_id: int) -> list[int]:
        """Получение входящих запросов на дружбу"""
        document = await self.collection.find_one({"user_id": user_id})
        print(document)
        return document.get("requests", []) if document else []
    
    async def add_friend_request(self, user_id: int, requester_id: int, requester_username: str):
        """Добавление запроса на дружбу"""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"requests": (requester_id, requester_username)}},
            upsert=True
        )
    
    async def remove_friend_request(self, user_id: int, requester_id: int):
        """Удаление запроса на дружбу по ID пользователя"""
        requester_id_str = str(requester_id)
        
        await self.collection.update_one(
            {"user_id": user_id},
            {"$pull": {
                "requests": {
                    "$elemMatch": {"$eq": requester_id_str}
                }
            }}
        )
        
    async def clear_friend_requests(self, user_id: int):
        """Очистка всех запросов на дружбу"""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"requests": []}}
        )
    async def clear_cache(self):
        """Удаление всего кеша пользователей"""
        await self.collection.delete_many({})


class Referrals:
    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        mongo_db_name: str = "habit_quest",
        mongo_collection: str = "referrals"
    ):
        self.mongo_db = mongo_client[mongo_db_name]
        self.collection = self.mongo_db[mongo_collection]
    
    async def initialize(self):
        """Создаем индекс по user_id и referral_id для быстрого поиска"""
        await self.collection.create_index([("user_id", 1), ("referral_id", 1)], unique=True)
    
    async def add_referral(self, user_id: int, referral_id: int, referral_data: Optional[dict] = None):
        """
        Добавляет нового реферала для пользователя.
        :param user_id: ID пользователя, который пригласил
        :param referral_id: ID приглашенного пользователя
        :param referral_data: Дополнительные данные о реферале (опционально)
        """
        referral_record = {
            "user_id": user_id,
            "referral_id": referral_id,
            "date_added": datetime.utcnow(),
            "referral_data": referral_data or {}
        }
        try:
            await self.collection.insert_one(referral_record)
        except Exception as e:
            # Можно обработать ошибку дублирования или логировать
            pass
    
    async def get_referrals(self, user_id: int) -> List[dict]:
        """
        Получает список всех рефералов пользователя.
        :param user_id: ID пользователя
        :return: список рефералов
        """
        cursor = self.collection.find({"user_id": user_id})
        return await cursor.to_list(length=None)
    
    async def count_referrals(self, user_id: int) -> int:
        """
        Подсчитывает количество рефералов у пользователя.
        :param user_id: ID пользователя
        :return: число рефералов
        """
        count = await self.collection.count_documents({"user_id": user_id})
        return count
    
    async def get_all_referrals(self) -> List[dict]:
        """
        Получает все записи рефералов (можно использовать для аналитики).
        :return: список всех рефералов
        """
        cursor = self.collection.find()
        return await cursor.to_list(length=None)
    
    async def remove_referral(self, user_id: int, referral_id: int):
        """
        Удаляет конкретного реферала.
        :param user_id: ID пользователя-реферера
        :param referral_id: ID реферала
        """
        await self.collection.delete_one({"user_id": user_id, "referral_id": referral_id})
    async def is_referral_in_user_referrals(self, referral_id: int, user_id: int) -> bool:
        """
        Проверяет, есть ли у пользователя с user_id2 реферал с referral_id1.
        :param referral_id: ID реферала, который ищем
        :param user_id: ID пользователя, у которого ищем реферал
        :return: True если есть, иначе False
        """
        count = await self.collection.count_documents({
            "user_id": user_id,
            "referral_id": referral_id
        })
        return count > 0

class UserMicroChallenge:
    def __init__(
        self,
        mongo_client: AsyncIOMotorClient,
        mongo_db_name: str = "habit_quest",
        mongo_collection: str = "user_micro_challenges"
    ):
        self.mongo_db = mongo_client[mongo_db_name]
        self.collection = self.mongo_db[mongo_collection]
    
    async def initialize(self):
        """Создаем индексы при инициализации"""
        await self.collection.create_index("user_id", unique=True)
    
    async def get_user_data(self, user_id: int) -> dict:
        """Получаем данные пользователя или создаем новый документ"""
        user_data = await self.collection.find_one({"user_id": user_id})
        if not user_data:
            user_data = {
                "user_id": user_id,
                "current_challenge": None,
                "challenge_levels": {},
                "last_response_date": datetime.utcnow()
            }
            await self.collection.insert_one(user_data)
        return user_data
    
    async def create_or_update_challenge(
        self,
        user_id: int,
        challenge_type: str,
        start_date: Optional[datetime] = None,
        personal_record: int = 0,
        new_habits: Optional[List[str]] = None,
        level: Optional[int] = None
    ):
        """
        Создает или обновляет текущий микрочеллендж пользователя
        
        :param user_id: ID пользователя
        :param challenge_type: Тип микрочелленджа
        :param start_date: Дата начала челленджа
        :param personal_record: Личный рекорд
        :param new_habits: Список новых привычек
        :param level: Опциональный параметр уровня
        """
        now = datetime.utcnow()
        if start_date is None:
            start_date = now
        
        # Получаем текущие данные пользователя
        user_data = await self.get_user_data(user_id)
        challenge_levels = user_data.get("challenge_levels", {})
        
        # Определяем уровень для челленджа
        if level is not None:
            new_level = level
        else:
            new_level = challenge_levels.get(challenge_type, 1)
        
        # Обновляем уровень в истории
        challenge_levels[challenge_type] = new_level
        
        # Формируем данные челленджа
        challenge_data = {
            "type": challenge_type,
            "level": new_level,
            "start_date": start_date,
            "personal_record": personal_record,
            "new_habits": new_habits or [],
            "last_update": now
        }
        
        # Обновляем документ пользователя
        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "current_challenge": challenge_data,
                    "challenge_levels": challenge_levels,
                    "last_response_date": now
                }
            }
        )
    
    async def increase_level(
        self,
        user_id: int,
        increment: int = 1
    ) -> Optional[int]:
        """
        Повышает уровень текущего челленджа
        
        :param user_id: ID пользователя
        :param increment: Значение увеличения уровня
        :return: Новый уровень или None если челлендж не активен
        """
        user_data = await self.get_user_data(user_id)
        if not user_data.get("current_challenge"):
            return None
        
        challenge_type = user_data["current_challenge"]["type"]
        new_level = user_data["current_challenge"]["level"] + increment
        
        # Обновляем уровень в истории
        challenge_levels = user_data.get("challenge_levels", {})
        challenge_levels[challenge_type] = new_level
        
        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "current_challenge.level": new_level,
                    "challenge_levels": challenge_levels,
                    "last_response_date": datetime.utcnow()
                }
            }
        )
        return new_level
    
    async def get_level(
        self,
        user_id: int,
        challenge_type: str
    ) -> int:
        """
        Получает текущий уровень для типа челленджа
        :return: Текущий уровень (1 если не найден)
        """
        user_data = await self.get_user_data(user_id)
        return user_data.get("challenge_levels", {}).get(challenge_type, 1)
    
    async def set_level(
        self,
        user_id: int,
        challenge_type: str,
        new_level: int
    ):
        """Устанавливает новый уровень для типа челленджа"""
        user_data = await self.get_user_data(user_id)
        challenge_levels = user_data.get("challenge_levels", {})
        challenge_levels[challenge_type] = new_level
        
        update_data = {
            "challenge_levels": challenge_levels,
            "last_response_date": datetime.utcnow()
        }
        
        # Если активный челлендж совпадает с типом, обновляем и его уровень
        if user_data.get("current_challenge") and user_data["current_challenge"]["type"] == challenge_type:
            update_data["current_challenge.level"] = new_level
        
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    
    async def get_challenge(self, user_id: int) -> Optional[dict]:
        """Получить текущий активный челлендж пользователя"""
        user_data = await self.get_user_data(user_id)
        return user_data.get("current_challenge")
    
    async def update_personal_record(
        self, 
        user_id: int,
        reset: bool = False
    ):
        """Обновление рекорда для текущего челленджа"""
        now = datetime.utcnow()
        user_data = await self.get_user_data(user_id)
        
        if not user_data.get("current_challenge"):
            return
        
        challenge_type = user_data["current_challenge"]["type"]
        last_update = user_data["current_challenge"].get("last_update", now)
        personal_record = user_data["current_challenge"].get("personal_record", 0)
        hours_passed = (now - last_update).total_seconds() / 3600

        if reset or hours_passed > 47:
            new_record = 1
        else:
            new_record = personal_record + 1

        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "current_challenge.personal_record": new_record,
                    "current_challenge.last_update": now,
                    "last_response_date": now
                }
            }
        )
    
    async def add_new_habits(
        self, 
        user_id: int,
        habits: List[str]
    ):
        """Добавить новые привычки в текущий челлендж"""
        user_data = await self.get_user_data(user_id)
        if not user_data.get("current_challenge"):
            return
        
        current_habits = user_data["current_challenge"].get("new_habits", [])
        updated_habits = list(set(current_habits + habits))
        
        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "current_challenge.new_habits": updated_habits,
                    "last_response_date": datetime.utcnow()
                }
            }
        )
    
    async def remove_habit(
        self, 
        user_id: int,
        habit: str
    ):
        """Удалить привычку из текущего челленджа"""
        user_data = await self.get_user_data(user_id)
        if not user_data.get("current_challenge"):
            return
        
        current_habits = user_data["current_challenge"].get("new_habits", [])
        if habit in current_habits:
            updated_habits = [h for h in current_habits if h != habit]
            await self.collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "current_challenge.new_habits": updated_habits,
                        "last_response_date": datetime.utcnow()
                    }
                }
            )
    
    async def delete_challenge(
        self, 
        user_id: int
    ):
        """Удалить текущий челлендж (сохраняя уровень в истории)"""
        await self.collection.update_one(
            {"user_id": user_id},
            {
                "$set": {"current_challenge": None},
                "$currentDate": {"last_response_date": True}
            }
        )
    
    async def update_last_response(
        self, 
        user_id: int
    ):
        """Обновить дату последнего ответа пользователя"""
        await self.collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_response_date": datetime.utcnow()}}
        )
    
    async def get_inactive_users(
        self, 
        days_inactive: int = 7
    ) -> List[dict]:
        """
        Получить пользователей с неактивными челленджами
        :param days_inactive: Количество дней без ответа
        :return: Список документов пользователей
        """
        threshold_date = datetime.utcnow() - timedelta(days=days_inactive)
        cursor = self.collection.find({
            "last_response_date": {"$lt": threshold_date},
            "current_challenge": {"$ne": None}
        })
        return await cursor.to_list(length=None)

async def get_delayed_messages(chat_id: int) -> list:
    """Возвращает все отложенные сообщения для указанного chat_id"""
    try:
        # Получаем все задачи из отложенной очереди
        messages = await rdb.zrange("delayed_messages", 0, -1, withscores=False)
        
        result = []
        for msg_json in messages:
            try:
                task_data = json.loads(msg_json)
                
                # Проверяем тип задачи и chat_id
                if task_data.get("type") == "send_message" and task_data.get("chat_id") == chat_id:
                    # Добавляем только нужные поля
                    result.append({
                        "message": task_data.get("message"),
                        "delay": task_data.get("delay"),
                        "repeat": task_data.get("repeat"),
                        "execute_at": await rdb.zscore("delayed_messages", msg_json)
                    })
            except json.JSONDecodeError:
                continue
        
        return result
    except Exception as e:
        print(f"Ошибка при получении отложенных сообщений: {e}")
        return []
def calculate_next_run(interval_type: str, interval_value: int) -> float:
    now = datetime.now()
    
    if interval_type == "seconds":
        next_run = now + timedelta(seconds=interval_value)
    elif interval_type == "minutes":
        next_run = now + timedelta(minutes=interval_value)
    elif interval_type == "hours":
        next_run = now + timedelta(hours=interval_value)
    elif interval_type == "days":
        next_run = now + timedelta(days=interval_value)
    elif interval_type == "weeks":
        next_run = now + timedelta(weeks=interval_value)
    elif interval_type == "months":
        total_months = now.month + interval_value
        year = now.year + (total_months - 1) // 12
        month = (total_months - 1) % 12 + 1
        
        try:
            next_run = now.replace(year=year, month=month)
        except ValueError:
            next_run = datetime(year, month, 1) + timedelta(days=32)
            next_run = next_run.replace(day=1) - timedelta(days=1)
            next_run = next_run.replace(
                hour=now.hour,
                minute=now.minute,
                second=now.second,
                microsecond=now.microsecond
            )
    elif interval_type == "years":
        year = now.year + interval_value
        try:
            next_run = now.replace(year=year)
        except ValueError:
            next_run = now.replace(year=year, month=3, day=1)
            next_run -= timedelta(days=1)
            next_run = next_run.replace(
                hour=now.hour,
                minute=now.minute,
                second=now.second,
                microsecond=now.microsecond
            )
    else:
        raise ValueError(f"Unsupported interval type: {interval_type}")
    
    return next_run.timestamp()


async def schedule_message(
    chat_id: int,
    message: str,
    delay: int,
    reply_markup: dict = None,
    repeat: dict = None,
    hide: bool = False
):
    """
    Постановка задачи на отправку сообщения.
    
    :param chat_id: ID чата
    :param message: Текст сообщения
    :param delay: Задержка в секундах до отправки
    :param reply_markup: Опциональный словарь с клавиатурой (или None)
    :param repeat: Настройки повторения (None для разовой отправки)
        Пример:
        {
            "interval_type": "days",  # days, hours, minutes, weeks, months
            "interval_value": 1,      # Каждые 1 день
            "end_at": None             # Окончание повторений (timestamp)
        }
    """
    task = {
        "type": "send_message",
        "chat_id": chat_id,
        "message": message,
        'delay': delay,
        'hide': hide
    }

    # Добавляем reply_markup, если он есть
    if reply_markup is not None:
        task['reply_markup'] = json.dumps(reply_markup)

    # Добавляем настройки повторения, если есть
    if repeat is not None:
        task['repeat'] = repeat

        # Если есть end_at, добавляем его в задачу
        if 'end_at' in repeat and repeat['end_at'] is not None:
            task['repeat']['end_at'] = repeat['end_at']

    print("Запланированная задача:", task)

    task_json = json.dumps(task)

    execute_at = time.time() + delay if delay > 0 else time.time()

    if delay > 0:
        await rdb.zadd("delayed_messages", {task_json: execute_at})
        print(f"Задача запланирована через {delay} секунд")
    else:
        await rdb.lpush("task_queue", task_json)
        print("Задача добавлена в очередь немедленно")
        
        
async def get_delayed_messages(chat_id: int) -> list:
    """Возвращает все отложенные сообщения для указанного chat_id с учетом hide"""
    try:
        # Получаем все сообщения из delayed_messages
        messages = await rdb.zrange("delayed_messages", 0, -1)
        
        result = []
        for msg_json in messages:
            try:
                task_data = json.loads(msg_json)
                
                # Проверяем тип и chat_id
                if task_data.get("type") == "send_message" and task_data.get("chat_id") == chat_id:
                    # Фильтр по hide: включаем только если hide=False или если нужно получать все
                    # В вашем случае — только hide=False
                    if not task_data.get("hide", False):
                        result.append({
                            "message": task_data.get("message"),
                            "delay": task_data.get("delay"),
                            "repeat": task_data.get("repeat"),
                            "execute_at": await rdb.zscore("delayed_messages", msg_json)
                        })
            except json.JSONDecodeError:
                continue
        
        return result
    except Exception as e:
        print(f"Ошибка при получении отложенных сообщений: {e}")
        return []
    
async def delete_delayed_message(chat_id: int, message_text: str) -> bool:
    """Удаляет отложенное сообщение по chat_id и тексту сообщения"""
    try:
        messages = await rdb.zrange("delayed_messages", 0, -1, withscores=False)
        deleted = False
        
        for msg_json in messages:
            try:
                task_data = json.loads(msg_json)
                
                # Ищем совпадение по типу, chat_id и тексту сообщения
                if (task_data.get("type") == "send_message" and 
                    task_data.get("chat_id") == chat_id and 
                    task_data.get("message") == message_text):
                    
                    # Удаляем из отложенной очереди
                    await rdb.zrem("delayed_messages", msg_json)
                    deleted = True
                    print(f"Сообщение удалено: chat_id={chat_id}, text='{message_text}'")
            except json.JSONDecodeError:
                continue
        
        return deleted
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
        return False