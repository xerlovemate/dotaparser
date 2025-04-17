from aiogram import Router, Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import requests
from sqlalchemy import select

import config
import handlers.utils
from database.models import User, async_session

API_TOKEN = config.TOKEN
CRYPTO_TOKEN = config.CRYPTO_TOKEN
bot = Bot(token=API_TOKEN)
router = Router()

invoices = {}


async def get_pay_link(amount):
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN}
    data = {"asset": "USDT", "amount": amount}

    try:
        response = requests.post('https://pay.crypt.bot/api/createInvoice', headers=headers, json=data)
        if response.ok:
            response_data = response.json()
            return response_data['result']['pay_url'], response_data['result']['invoice_id'], amount  # Возвращаем сумму
        else:
            print(f"Ошибка при создании инвойса: {response.status_code}, {response.text}")
            return None, None, None
    except Exception as e:
        print(f"Ошибка при создании инвойса: {e}")
        return None, None, None


async def check_payment_status(invoice_id):
    headers = {
        "Crypto-Pay-API-Token": CRYPTO_TOKEN,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post('https://pay.crypt.bot/api/getInvoices', headers=headers, json={})
        if response.ok:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Ошибка при проверке статуса оплаты: {e}")
        return None


async def update_user_balance(tg_id, amount):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if user:
            user.balance += amount
            await session.commit()
            return True

        return False


@router.callback_query(F.data == 'depozit')
async def recharge_balance(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='3.0 USDT', callback_data='3.0'),
         InlineKeyboardButton(text='5.0 USDT', callback_data='5.0')],
        [InlineKeyboardButton(text='10.0 USDT', callback_data='10.0'),
         InlineKeyboardButton(text='25.0 USDT', callback_data='25.0')],
        [InlineKeyboardButton(text='50.0 USDT', callback_data='50.0')],
        [InlineKeyboardButton(text='Ввести сумму вручную', callback_data='custom_amount')],
        [InlineKeyboardButton(text='В меню', callback_data='back_to_main_menu')]
    ])
    text = 'Выберите сумму для пополнения'
    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode='HTML')
    await state.clear()


class DepositState(StatesGroup):
    waiting_for_amount = State()


@router.callback_query(F.data == 'custom_amount')
async def ask_for_custom_amount(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data='depozit')]
    ])
    await callback.message.edit_text(
        text="Введите сумму в USDT, например: <b>7.5</b>",
        parse_mode='HTML',
        reply_markup=kb
    )
    await state.set_state(DepositState.waiting_for_amount)

    await state.update_data(bot_message_id=callback.message.message_id)


@router.message(DepositState.waiting_for_amount)
async def process_custom_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount < 1.0:
            await message.delete()
            await message.answer("❗ Минимальная сумма — 1.0 USDT.", reply_markup=handlers.utils.ponyal_kb)
            return

        await message.delete()

        data = await state.get_data()
        bot_msg_id = data.get("bot_message_id")

        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=bot_msg_id,
            text=f'Создается ссылка для оплаты...',
            parse_mode='HTML'
        )

        pay_link, invoice_id, amount = await get_pay_link(amount)
        if pay_link and invoice_id:
            invoices[message.chat.id] = {'invoice_id': invoice_id, 'amount': amount}
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f'Оплатить {amount} USDT', url=pay_link)],
                [InlineKeyboardButton(text='Проверить оплату', callback_data=f'check_payment_{invoice_id}')],
                [InlineKeyboardButton(text='Отмена', callback_data='depozit')]
            ])
            if bot_msg_id:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=bot_msg_id,
                    text=f'Ссылка для оплаты <b>{amount} USDT</b>:',
                    reply_markup=kb,
                    parse_mode='HTML'
                )
            else:
                # fallback: если нет ID сообщения, просто отправим новое
                sent = await message.answer(f'Ссылка для оплаты <b>{amount} USDT</b>:', reply_markup=kb, parse_mode='HTML')
                await state.update_data(bot_message_id=sent.message_id)
        else:
            await message.answer("❗ Не удалось создать ссылку. Попробуйте позже.", reply_markup=handlers.utils.ponyal_kb)

        await state.clear()

    except ValueError:
        await message.delete()
        await message.answer("❗ Введите корректное число (например: 7.5)", reply_markup=handlers.utils.ponyal_kb)


@router.callback_query(F.data.in_(['3.0', '5.0', '10.0', '25.0', '50.0']))
async def process_payment(callback: CallbackQuery):
    amount = float(callback.data)
    chat_id = callback.message.chat.id
    pay_link, invoice_id, amount = await get_pay_link(amount)

    if pay_link and invoice_id:
        invoices[chat_id] = {'invoice_id': invoice_id, 'amount': amount}
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f'Оплатить {amount} USDT', url=pay_link)],
            [InlineKeyboardButton(text='Проверить оплату', callback_data=f'check_payment_{invoice_id}')],
            [InlineKeyboardButton(text='Отмена', callback_data='depozit')]
        ])
        text = f'Ссылка для оплаты <b>{amount} USDT</b>:'
        await callback.message.edit_text(text=text, reply_markup=kb, parse_mode='HTML')
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='В меню', callback_data='back_to_main_menu')]
        ])
        text = 'Ошибка: Не удалось создать счет на оплату. Попробуйте позже или свяжитесь с <b>@semyonsk</b>'
        await callback.message.edit_text(text=text, reply_markup=kb, parse_mode='HTML')


@router.callback_query(lambda call: call.data.startswith('check_payment_'))
async def check_payment(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    invoice_id = callback.data.split('check_payment_')[1]

    payment_status = await check_payment_status(invoice_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='В меню', callback_data='back_to_main_menu')]
    ])
    if payment_status and payment_status.get('ok'):
        if 'items' in payment_status['result']:
            invoice = next((inv for inv in payment_status['result']['items'] if str(inv['invoice_id']) == invoice_id),
                           None)
            if invoice:
                status = invoice['status']
                if status == 'paid':
                    # Оплата успешно получена, добавляем деньги на баланс пользователя
                    amount = invoices.get(chat_id, {}).get('amount', 0)  # Используем сохраненную сумму
                    if amount:
                        success = await update_user_balance(chat_id, amount)  # Добавляем на баланс
                        if success:
                            await callback.message.edit_text(
                                text=f'Оплата успешно получена! Баланс обновлен на <b>{amount} USDT</b>.',
                                reply_markup=kb, parse_mode='HTML')
                        else:
                            await callback.message.edit_text(text='Не удалось обновить баланс.',
                                                             reply_markup=kb, parse_mode='HTML')
                    else:
                        await callback.message.edit_text(text='Не удалось получить сумму для пополнения.',
                                                         reply_markup=kb, parse_mode='HTML')
                else:
                    await callback.answer('Оплата не найдена.', show_alert=True)
            else:
                await callback.answer('Счет не найден.', show_alert=True)
        else:
            await callback.answer('Ошибка при получении статуса оплаты.', show_alert=True)
    else:
        await callback.answer('Ошибка при получении статуса оплаты.', show_alert=True)
