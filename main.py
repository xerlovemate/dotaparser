import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.types import FSInputFile
from config import TOKEN
from database.models import async_main
from handlers import (
    start,
    pay,
    utils,
    admin,
    parse
)


async def main():
    await async_main()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_routers(
        start.router,
        pay.router,
        utils.router,
        admin.router,
        parse.router
    )

    task_polling = dp.start_polling(bot)

    await asyncio.gather(task_polling)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('иди нахуй')
