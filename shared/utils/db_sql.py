import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from shared.models.user import Base
from shared.models.user import User1
from datetime import datetime



DATABASE_URL = 'sqlite+aiosqlite:////app/data/users.db'
engine = create_async_engine(DATABASE_URL)




    
async_session = async_sessionmaker(engine, class_=AsyncSession)


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database creation error: {e}")
        raise
    
    
    
class UserService:
    @staticmethod
    def get_user_stats(user_id: int) -> dict:
        with async_session() as session:
            user = session.query(User1).filter(User1.id == user_id).first()
            if not user:
                # Создаем нового пользователя
                user = User1(id=user_id)
                session.add(user)
                session.commit()
            
            return {
                "stars": user.stars,
                "awards": user.awards,
                "streak": user.streak,
                "created_at": user.created_at,
                'target': user.target,
                'notification': user.notification
            }
    
    @staticmethod
    def update_user_stats(
        user_id: int,
        stars_delta: int = 0,
        awards_delta: int = 0,
        streak_delta: int = 0,
        target: str = None,
        notification: bool = True
    ):
        with async_session() as session:
            user = session.query(User1).filter(User1.id == user_id).first()
            if not user:
                user = User1(id=user_id)
                session.add(user)
            
            if stars_delta:
                user.stars += stars_delta
            if awards_delta:
                user.awards += awards_delta
            if streak_delta:
                user.streak += streak_delta
            if target:
                user.target = target
            if notification:
                user.notification = notification
            user.last_active = datetime.utcnow()
            session.commit()