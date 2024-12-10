import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiohttp import ClientSession, ClientError
from dotenv import load_dotenv
from db import Database

# Загрузка переменных окружения
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация базы данных и кэша
db = Database()

class Cache:
    def __init__(self):
        self.cache = {}

    def has(self, query):
        return query in self.cache

    def get(self, query):
        return self.cache.get(query)

    def set(self, query, data):
        self.cache[query] = data

cache = Cache()

# Определение состояний
class BotStates(StatesGroup):
    waiting_for_movie = State()

# Вспомогательная функция для получения данных о фильме
async def fetch_movie_data(query: str) -> dict:
    if cache.has(query):
        return cache.get(query)

    try:
        async with ClientSession() as session:
            async with session.get(f'http://www.omdbapi.com/?t={query}&apikey={OMDB_API_KEY}') as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("Response") == "True":
                    cache.set(query, data)
                    return data
                else:
                    logging.warning(f"Фильм не найден: {query}")
    except ClientError as e:
        logging.error(f"Ошибка сети: {e}")
    except Exception as e:
        logging.error(f"Ошибка при получении данных о фильме: {e}")
    return {}

# Подготовка текста ответа о фильме
def format_movie_response(movie_data: dict) -> str:
    title = movie_data.get("Title", "Неизвестно")
    year = movie_data.get("Year", "Неизвестно")
    rating = movie_data.get("imdbRating", "Нет рейтинга")
    plot = movie_data.get("Plot", "Описание отсутствует")
    link = f"https://www.imdb.com/title/{movie_data.get('imdbID', '')}"

    return (
        f"🎬 *{title}* ({year})\n\n"
        f"📊 Рейтинг IMDb: {rating}\n\n"
        f"📜 Сюжет: {plot}\n\n"
        f"🔗 [Ссылка на IMDb]({link})"
    )

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("Добро пожаловать! Я могу помочь вам найти информацию о фильмах. Просто напишите название фильма.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "Вот как использовать этого бота:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение помощи\n"
        "/history - Показать вашу историю поиска\n"
        "/stats - Показать вашу статистику поиска\n"
        "Просто напишите название фильма, чтобы найти информацию о нем!"
    )
    await message.reply(help_text)

@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    history = db.get_search_history(user_id)
    if history:
        history_text = "\n".join([f"{i + 1}. {query}" for i, query in enumerate(history)])
        await message.reply(f"Ваши последние 10 поисков:\n{history_text}")
    else:
        await message.reply("Ваша история поиска пуста.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    count = db.get_user_stats(user_id)
    await message.reply(f"Вы искали информацию о {count} фильмах.")

# Основной обработчик сообщений
@dp.message(F.text)
async def handle_movie_query(message: types.Message):
    query = message.text.strip()
    movie_data = await fetch_movie_data(query)

    if movie_data:
        response_text = format_movie_response(movie_data)
        poster = movie_data.get("Poster", "")

        db.save_search_history(message.from_user.id, query)

        if poster and poster != "N/A":
            await message.reply_photo(poster, caption=response_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Я не смог найти информацию об этом фильме. Пожалуйста, попробуйте другой запрос.")

# Обработчик ошибок
@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    logging.error(f"Обновление {update} вызвало ошибку: {exception}")
    if hasattr(update, 'message'):
        await update.message.reply("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.")

# Основная функция для запуска бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
