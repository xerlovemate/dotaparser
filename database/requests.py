from database.models import async_session, User
from sqlalchemy import select, func, delete
from aiogram import Bot
from config import TOKEN

bot = Bot(token=TOKEN)


async def set_user(tg_id: int, username: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User).where(User.tg_id == tg_id)
            )
            user = result.scalar_one_or_none()

            if user:
                user.tg_username = username
            else:
                user = User(
                    tg_id=tg_id,
                    tg_username=username
                )
                session.add(user)

            await session.commit()


async def get_balance_by_tg_id(tg_id: int) -> float:
    async with async_session() as session:
        result = await session.execute(select(User.balance).filter(User.tg_id == tg_id))
        balance = result.scalars().first()

        if balance is None:
            return 0.00

        return round(balance, 3)


async def get_trial_by_tg_id(tg_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(select(User.trial).filter(User.tg_id == tg_id))
        trial = result.scalars().first()

        return trial


async def add_balance_to_user(tg_id: int, amount: float):
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if user:
            user.balance = amount
            await session.commit()
            return True
        else:
            return False


async def trial_minus(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if user:
            user.trial -= 1
            await session.commit()
            return True
        else:
            return False


async def balance_minus(tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).filter(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if user:
            user.balance -= 0.01
            await session.commit()
            return True
        else:
            return False
