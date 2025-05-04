# Цель проекта
- Дать возможность пользователям парсить данные о игроках Dota2 в формате удобного ТГ-бота
- Получить прибыль с монетизации (к боту подключен CryptoBot для оплаты с помощью USDT)

# Зависимости
- Aiogram 3
- BS4
- SQLAlchemy, aiosqlite
- requests

# Настройка
- Для начала необходимо создать виртуальное окружение и установить в него зависимости

`pip install aiogram, bs4, requests, SQLAlchmey, aiosqlite`

- Затем создаем бота через [BotFather](https://t.me/botfather), полученный API key вставляем в переменную **TOKEN** в config.py
- Создаем криптомагазин в [CryptoBot](https://t.me/cryptobot), также вставляем API key в переменную **CRYPTO_TOKEN**
- Запускаем бота через файл **main.py**
