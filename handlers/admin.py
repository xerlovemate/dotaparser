from aiogram import Router, Bot, F, types
from aiogram.filters import Command
import database.requests as rq
import config
import handlers.utils

router = Router()
router.message.filter(F.chat.type == 'private')
API_TOKEN = config.TOKEN

bot = Bot(token=API_TOKEN)


@router.message(Command("balance"))
async def cmd_add_balance(message: types.Message):
    if message.from_user.id != 450997363:
        return

    try:
        command, tg_id, amount = message.text.split()
        tg_id = int(tg_id)
        amount = float(amount)
    except ValueError:
        await message.answer("Неверный формат команды. \nИспользуйте: <code>/balance tg_id amount</code>",
                             parse_mode='HTML', reply_markup=handlers.utils.ponyal_kb)
        return

    success = await rq.add_balance_to_user(tg_id, amount)

    if success:
        await message.answer(f"Баланс пользователя с tg_id <code>{tg_id}</code> был успешно изменен"
                             f" на <b>{amount}</b>!",
                             parse_mode='HTML',
                             reply_markup=handlers.utils.ponyal_kb)
    else:
        await message.answer(f"Пользователь с tg_id <code>{tg_id}</code> не найден.",
                             reply_markup=handlers.utils.ponyal_kb)
