from sqlalchemy import BigInteger, String, DateTime, Integer, Column, Boolean, ForeignKey, Text, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

# Создание движка для асинхронного взаимодействия с базой данных SQLite
engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3')

# Создание асинхронной сессии для работы с базой данных
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


class User(Base):
    """Класс пользователей"""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)

    tg_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    tg_username: Mapped[str] = mapped_column(String, nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.00)

    trial: Mapped[int] = mapped_column(Integer, default=100)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
