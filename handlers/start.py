from aiogram import Router, Bot, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, CallbackQuery
from sqlalchemy.future import select

import config
import database.requests as rq
from database.models import async_session, User

router = Router()
router.message.filter(F.chat.type == 'private')
API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)


# ================== /start handler ==================
@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(tg_id=message.from_user.id, username=message.from_user.username)
    text = (f'<b>Баланс: {await rq.get_balance_by_tg_id(message.from_user.id)} USDT</b>\n'
            f'<b>Бесплатных запросов: {await rq.get_trial_by_tg_id(message.from_user.id)}</b>')

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦞 Парсить", callback_data="parse_menu")],
        [InlineKeyboardButton(text="💳 Пополнить", callback_data='depozit')]
    ])

    await message.answer(text=text, reply_markup=markup, parse_mode="HTML")


@router.callback_query(F.data == 'back_to_main_menu')
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    text = (f'<b>Баланс: {await rq.get_balance_by_tg_id(callback.from_user.id)} USDT</b>\n'
            f'<b>Бесплатных запросов: {await rq.get_trial_by_tg_id(callback.from_user.id)}</b>')
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦞 Парсить", callback_data="parse_menu")],
        [InlineKeyboardButton(text="💳 Пополнить", callback_data='depozit')]
    ])
    await callback.message.edit_text(text=text, reply_markup=markup, parse_mode="HTML")
    await state.clear()
