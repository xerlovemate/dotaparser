from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from sqlalchemy.future import select

import config
import database.requests as rq
from database.models import async_session, User

router = Router()
router.message.filter(F.chat.type == 'private')
API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)

ponyal_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Понял', callback_data='ponyal')]
])

delete_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Удалить', callback_data='ponyal')]
])


@router.callback_query(F.data == 'ponyal')
async def delete_notification(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
