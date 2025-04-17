import re
import aiohttp
from aiogram import Router, Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import requests
from bs4 import BeautifulSoup
from sqlalchemy import select
import database.requests as rq
import config
import handlers.utils
from database.models import User, async_session

API_TOKEN = config.TOKEN
CRYPTO_TOKEN = config.CRYPTO_TOKEN
bot = Bot(token=API_TOKEN)
router = Router()


async def parse_most_played_heroes(steam_id: int) -> str:
    url = f"https://www.dotabuff.com/players/{steam_id}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # Сначала получаем куки с главной страницы
        async with session.get("https://www.dotabuff.com") as _:
            pass  # просто для получения куки

        async with session.get(url) as response:
            if response.status != 200:
                return f"❌ Ошибка {response.status} при запросе Dotabuff."
            text = await response.text()

    soup = BeautifulSoup(text, "html.parser")
    table = soup.find("div", class_="r-table r-only-mobile-5 heroes-overview")
    if not table:
        return "❌ Таблица 'Most Played Heroes' не найдена."

    rows = table.find_all("div", class_="r-row")
    if not rows:
        return "❌ Не удалось найти строки таблицы."

    result_lines = ["🔥 Сигнатурки:"]
    for idx, row in enumerate(rows[:5], start=1):
        cols = row.find_all("div", recursive=False)
        if len(cols) < 6:
            continue

        hero_raw = cols[0].text.strip()
        hero = re.sub(r'^Hero', '', hero_raw).strip()
        hero = re.sub(r'\d{4}-\d{2}-\d{2}$', '', hero).strip()

        matches = re.sub(r'^Matches', '', cols[1].text.strip())
        winrate = re.sub(r'^Win %', '', cols[2].text.strip())
        kda = re.sub(r'^KDA', '', cols[3].text.strip())

        role_raw = cols[4].text.strip()
        role = re.sub(r'^Role', '', role_raw).split()[0]

        lane_raw = cols[5].text.strip()
        lane = re.sub(r'^Lane', '', lane_raw).split()[0] + " Lane"

        result_lines.append(f"{idx}. {hero} — {matches} матчей | {winrate} | {kda} | {role} | {lane}")

    return "\n".join(result_lines)


class ParseStates(StatesGroup):
    waiting_for_numbers = State()


@router.callback_query(F.data == 'parse_menu')
async def parse_menu(callback: CallbackQuery, state: FSMContext):
    text = (f'<b>Бесплатных запросов: {await rq.get_trial_by_tg_id(callback.from_user.id)}</b>\n\n'
            f'<b>Баланс: {await rq.get_balance_by_tg_id(callback.from_user.id)} USDT</b>\n'
            f'<b>Цена одного запроса 0.01 USDT</b>\n'
            f'<b>Отправь цифры, например <code>321580662</code></b>')
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Отмена', callback_data='back_to_main_menu')]
    ])

    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode='HTML')
    await state.set_state(ParseStates.waiting_for_numbers)


@router.message(ParseStates.waiting_for_numbers)
async def handle_numbers(message: types.Message, state: FSMContext):
    numbers = message.text.strip()

    if not numbers.isdigit():
        await message.answer("❗ Отправь только цифры, без пробелов или символов.")
        return

    trial = await rq.get_trial_by_tg_id(message.from_user.id)
    if trial:
        await rq.trial_minus(message.from_user.id)
    else:
            balance = await rq.get_balance_by_tg_id(message.from_user.id)
            if balance > 0:
                await rq.balance_minus(message.from_user.id)
            else:
                cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Отмена', callback_data='back_to_main_menu')]
                ])
                await message.answer(text='<b>Недостаточно средств.</b>',
                                        reply_markup=cancel_kb, parse_mode='HTML')
                return

    account_id = numbers
    headers = {'accept': 'application/json'}
    base_url = 'https://api.opendota.com/api/players'

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(f'{base_url}/{account_id}') as resp1:
                data_base_info = await resp1.json()

            async with session.get(f'{base_url}/{account_id}/wl', params={'limit': 20}) as resp2:
                data_wl_info = await resp2.json()

            async with session.get(f'{base_url}/{account_id}/wl') as resp3:
                data_total_wl = await resp3.json()

            async with session.get(f'{base_url}/{account_id}/matches', params={'limit': 1}) as resp4:
                data_matches = await resp4.json()
        except Exception as e:
            await message.answer("❌ Ошибка при получении данных с OpenDota API.")
            print(f"[OpenDota ERROR] {e}")
            return

    try:
        st_id = data_base_info['profile']['account_id']
        avatar = data_base_info['profile']['avatarfull']
        name = data_base_info['profile']['personaname']
        profile_url = data_base_info['profile']['profileurl']
    except KeyError:
        await message.answer("❗ Не удалось получить профиль. Проверь ID и попробуй снова.")
        return

    try:
        kills = data_matches[0]['kills']
        deaths = data_matches[0]['deaths']
        assists = data_matches[0]['assists']
    except:
        kills = 0
        deaths = 0
        assists = 0

    last_match_id = data_matches[0]['match_id']
    win = data_wl_info.get('win', 0)
    lose = data_wl_info.get('lose', 0)
    winrate = round((win / (win + lose) * 100) if (win + lose) > 0 else 0, 2)

    total_wins = data_total_wl.get('win', 0)
    total_loses = data_total_wl.get('lose', 0)
    total_games = total_wins + total_loses
    total_winrate = round((total_wins / total_games * 100) if total_games > 0 else 0, 2)

    first_text = (
        f'<b>Account ID: <code>{st_id}</code></b>\n\n'
        f'<b>{name}</b>\n'
        f'<b>Steam профиль: <a href="{profile_url}">*тык*</a></b>\n'
        f'<b>DotaBuff: <a href="https://www.dotabuff.com/players/{numbers}">*тык*</a></b>\n\n'
        f'<b>Винрейт за последние 20 игр: {winrate}%</b>\n'
        f'<b>Общий винрейт: {total_winrate}% ({total_wins}/{total_loses})</b>\n'
        f'<b>Всего игр: {total_games}</b>\n\n'
        f'<b>Последняя игра: {kills}/{deaths}/{assists}</b>\n'
        f'<b>ID последней игры: <code>{last_match_id}</code></b>'
    )

    await message.answer(text=first_text, parse_mode='HTML')

    second_text = f"<b>{await parse_most_played_heroes(numbers)}</b>"
    await message.answer(text=second_text, parse_mode='HTML')

    await handlers.start.cmd_start(message)
    await state.clear()
