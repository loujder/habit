from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, select, Boolean
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime


"""
модели для NOSQL базы данных
"""
class Task(BaseModel):
    id: int
    datetime_registation: int = 0
    target_time: str = ''
    status: str = ''
    stars: int = 0
    awards: int = 0
    streak: int = 0
"""
модели для SQL базы данных
"""
class Base(DeclarativeBase):
    pass


class User1(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    stars = Column(Integer, default=0)
    awards = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    stars = Column(Integer, default=0)
    status = Column(String, default='user')
    target = Column(String, default='Здесь пока пусто...')
    notification = Column(Boolean, default=True)
    premium_expiry = Column(DateTime, nullable=True)