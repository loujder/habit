import asyncio
import json
import time
import signal
from aiogram import Bot
from shared.utils.db_nosql import rdb
from shared.utils.config import settings
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton   
from shared.utils.db_nosql import UserCache, UserFriends, UserMicroChallenge
from motor.motor_asyncio import AsyncIOMotorClient
from aiogram.client.default import DefaultBotProperties

mongo_client = AsyncIOMotorClient(
    f'mongodb://{settings.MONGO_USERNAME}:'
    f'{settings.MONGO_PASSWORD}@'
    f'{settings.MONGO_HOST}:'
    f'{settings.MONGO_PORT}'
)

external_client = AsyncIOMotorClient(
    f'mongodb://{settings.MONGO_USERNAME}:'
    f'{settings.MONGO_PASSWORD}@'
    f'{settings.MONGO_HOST_EXTERNAL}:'
    f'{settings.MONGO_PORT_EXTERNAL}'
)


user_cache = UserCache(
    mongo_client=mongo_client,
    mongo_db_name=settings.MONGO_DB_NAME,
    mongo_collection=settings.MONGO_COLLECTION
)

user_microchalenges = UserMicroChallenge(mongo_client=mongo_client)


# Глобальная переменная для управления выполнением
running = True

class MessageWorker:
    def __init__(self, bot_token: str):
        self.bot = Bot(token=bot_token,default=DefaultBotProperties(parse_mode="HTML"))
        print("Бот для отправки сообщений инициализирован")
    
    async def send_message(self, chat_id: int, message: str, reply_markup=None):
        """Отправка сообщения через Telegram API с опциональной клавиатурой"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=reply_markup
            )
            print(f"Сообщение отправлено в chat_id={chat_id}")
            return True
        except Exception as e:
            print(f"Ошибка отправки сообщения в {chat_id}: {e}")
            return False

def calculate_next_run(interval_type: str, interval_value: int) -> float:
    """Вычисляет timestamp следующего выполнения"""
    now = datetime.now()
    if interval_type == "days":
        next_run = now + timedelta(days=interval_value)
    elif interval_type == "hours":
        next_run = now + timedelta(hours=interval_value)
    elif interval_type == "minutes":
        next_run = now + timedelta(minutes=interval_value)
    elif interval_type == "weeks":
        next_run = now + timedelta(weeks=interval_value)
    elif interval_type == "months":
        # Простая обработка месяцев (может быть не точной при переходе через границы месяцев)
        month = now.month - 1 + interval_value
        year = now.year + month // 12
        month = month % 12 + 1
        day = min(now.day, [31,
                            29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                            31,30,31,30,31,31,30,31,30,31][month-1])
        next_run = datetime(year, month, day)
    else:
        next_run = now + timedelta(days=1)  # По умолчанию ежедневно
    
    return next_run.timestamp()

async def process_message_task(worker: MessageWorker, task_data: dict):
    """Обработка задачи отправки сообщения с поддержкой повторений и клавиатуры"""
    try:
        chat_id = task_data['chat_id']
        message = task_data['message']
       
        
        reply_markup_json = task_data.get('reply_markup')
        reply_markup = None
        if reply_markup_json:
            keyboard_list = json.loads(reply_markup_json)
            print(keyboard_list)
            keyboard = [
                [InlineKeyboardButton(**btn) for btn in row]
                for row in keyboard_list
            ]
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        success = await worker.send_message(chat_id, message, reply_markup)

        # Обработка повторений ТОЛЬКО если указан флаг repeat
        if success and 'repeat' in task_data:
            interval_type = task_data['repeat']['interval_type']
            interval_value = task_data['repeat']['interval_value']
            end_at_ts = task_data['repeat'].get('end_at')

            # Проверяем не истек ли срок повторений
            if end_at_ts and time.time() > end_at_ts:
                print(f"Повторения для chat_id={chat_id} завершены")
                return True

            # Вычисляем следующее выполнение
            next_run_ts = calculate_next_run(interval_type, interval_value)

            # Создаем новую задачу с обновленным delay и last_sent
            new_task = {
                **task_data,
                "delay": max(0, next_run_ts - time.time()),
                "last_sent": time.time()
            }

            await enqueue_message(new_task)
            print(f"Запланировано повторное сообщение для chat_id={chat_id} через {interval_value} {interval_type}")
        else:
            print(f"Сообщение в chat_id={chat_id} отправлено один раз (без повторений)")
        
        return success
    except Exception as e:
        print(f"Ошибка обработки задачи: {e}")
        return False

async def retry_message(task_data: dict, max_retries: int=3):
    """Повторная отправка сообщения при неудаче"""
    try:
        retries = task_data.get("retries",0)+1
        if retries <= max_retries:
            task_data["retries"] = retries
            delay_seconds = min(300, 5 ** retries)  # экспоненциальный рост задержки до 5 минут
            
            task_data["delay"] = delay_seconds
            await enqueue_message(task_data)
            print(f"Повтор #{retries} для chat_id={task_data['chat_id']} через {delay_seconds} сек")
            return True
        else:
            print(f"Сообщение в chat_id={task_data['chat_id']} провалено после {max_retries} попыток")
            return False
    except Exception as e:
        print(f"Ошибка повтора сообщения: {e}")
        return False

async def enqueue_message(task_data: dict):
    """Добавление задачи в очередь или отложенную очередь"""
    try:
        task_json = json.dumps(task_data)
        delay_seconds = task_data.get('delay',0)

        if delay_seconds > 0:
            execute_at_ts = time.time() + delay_seconds
            await rdb.zadd("delayed_messages", {task_json: execute_at_ts})
            print(f"Отложенное сообщение запланировано на {delay_seconds} сек")
        else:
            await rdb.lpush("task_queue", task_json)
            print("Сообщение добавлено в очередь")
        
        return True
    except Exception as e:
        print(f"Ошибка добавления задачи: {e}")
        return False

async def task_worker(worker: MessageWorker):
    """Основной цикл воркера для обработки задач"""
    global running
    
    print("Воркер сообщений запущен")
    
    while running:
        try:
            # Получаем задачу из очереди с таймаутом 1 секунда
            task_raw = await rdb.brpop("task_queue", timeout=1)
            
            if task_raw:
                _, task_json = task_raw
                task_data = json.loads(task_json)

                if task_data.get("type") == "send_message":
                    success = await process_message_task(worker, task_data)
                else:
                    print(f"Неизвестный тип задачи: {task_data.get('type')}")
            
            await asyncio.sleep(0.1)  # короткая пауза для снижения нагрузки
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Ошибка в воркере: {e}")
    
    print("Воркер остановлен")

async def delayed_messages_handler(worker: MessageWorker):
    """Обработка отложенных сообщений"""
    global running
    
    print("Обработчик отложенных сообщений запущен")
    
    while running:
        try:
            current_time_ts = time.time()
            
            # Получаем все сообщения готовые к отправке (score <= current_time)
            messages_ready = await rdb.zrangebyscore("delayed_messages", 0, current_time_ts)

            for msg_json in messages_ready:
                await rdb.lpush("task_queue", msg_json)
                await rdb.zrem("delayed_messages", msg_json)
                msg_obj = json.loads(msg_json)
                print(f"Перенесено из отложенных в очередь: chat_id={msg_obj.get('chat_id')}")
            
            await asyncio.sleep(1)  # проверка каждую секунду
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Ошибка при обработке отложенных сообщений: {e}")

def handle_shutdown(signame):
    """Обработчик сигналов завершения"""
    global running
    print(f"Получен сигнал {signame}, остановка...")
    running=False

async def main():
    """Основная функция запуска воркера"""
    
    worker_instance=MessageWorker(settings.BOT_TOKEN)

    loop=asyncio.get_running_loop()
    for sig in ('SIGINT','SIGTERM'):
        loop.add_signal_handler(getattr(signal,sig), lambda s=sig: handle_shutdown(s))
    
    await asyncio.gather(
      task_worker(worker_instance),
      delayed_messages_handler(worker_instance),
      )
    
    await worker_instance.bot.session.close()
    print("Сессия бота закрыта")

if __name__=='__main__':
    print("Запуск системы обработки сообщений")
    
    try:
       asyncio.run(main())
       
    except KeyboardInterrupt:
        print("Работа прервана пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
    finally:
        print("Работа системы завершена")