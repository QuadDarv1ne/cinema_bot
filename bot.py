import os
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiohttp import ClientSession, ClientError
from dotenv import load_dotenv
from db import Database
import random

# Загрузка переменных окружения
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация базы данных
db = Database()

# Кэширование с использованием timedelta
class Cache:
    def __init__(self, expiration: timedelta = timedelta(minutes=10)):
        self.cache = {}
        self.expiration = expiration

    def has(self, query):
        if query in self.cache:
            timestamp, data = self.cache[query]
            if datetime.now() - timestamp < self.expiration:
                return True
            else:
                del self.cache[query]  # Удаляем устаревшие данные
        return False

    def get(self, query):
        return self.cache[query][1] if self.has(query) else None

    def set(self, query, data):
        self.cache[query] = (datetime.now(), data)

cache = Cache()

# Вспомогательная функция для получения данных о фильме
async def fetch_movie_data(query: str) -> dict:
    if cache.has(query):
        return cache.get(query)

    async with ClientSession() as session:
        try:
            async with session.get(f'http://www.omdbapi.com/?t={query}&apikey={OMDB_API_KEY}&plot=full') as response:
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
    genre = movie_data.get("Genre", "Неизвестно")
    director = movie_data.get("Director", "Неизвестно")
    actors = movie_data.get("Actors", "Неизвестно")
    rating = movie_data.get("imdbRating", "Нет рейтинга")
    plot = movie_data.get("Plot", "Описание отсутствует")
    awards = movie_data.get("Awards", "Нет наград")
    runtime = movie_data.get("Runtime", "Неизвестно")
    link = f"https://www.imdb.com/title/{movie_data.get('imdbID', '')}"

    return (
        f"🎬 *{title}* ({year})\n"
        f"📂 Жанр: {genre}\n"
        f"🎥 Режиссёр: {director}\n"
        f"🎭 Актёры: {actors}\n"
        f"⏳ Длительность: {runtime}\n"
        f"📊 Рейтинг IMDb: {rating}\n"
        f"🏆 Награды: {awards}\n"
        f"\n📜 Сюжет: {plot}\n"
        f"\n🔗 [Ссылка на IMDb]({link})"
    )

# Команды бота
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("Привет! Я помогу найти фильмы и сериалы. Напиши название, и я постараюсь найти информацию.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "Вот как использовать меня:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение помощи\n"
        "/history - Показать вашу историю поиска\n"
        "/stats - Статистика ваших поисков\n"
        "/random - Случайный фильм или сериал\n"
        "/search <название> - Найти фильм по названию\n"
        "/clearhistory - Очистить историю поиска\n"
        "/quote - Случайная цитата о кино\n"
    )
    await message.reply(help_text)

@dp.message(Command("history"))
async def cmd_history(message: types.Message):
    user_id = message.from_user.id
    history = await db.get_search_history(user_id)
    if history:
        history_text = "\n".join([f"{i + 1}. {query}" for i, query in enumerate(history)])
        await message.reply(f"Ваши последние 10 поисков:\n{history_text}")
    else:
        await message.reply("Ваша история поиска пуста.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    count = await db.get_user_stats(user_id)
    await message.reply(f"Вы искали информацию о {count} фильмах или сериалах.")

@dp.message(Command("random"))
async def cmd_random(message: types.Message):
    random_movies = ["The Shawshank Redemption", "The Godfather", "The Dark Knight", "Forrest Gump", "Inception"]
    random_movie = random.choice(random_movies)
    movie_data = await fetch_movie_data(random_movie)
    
    if movie_data:
        response_text = format_movie_response(movie_data)
        poster = movie_data.get("Poster", "")
        if poster and poster != "N/A":
            await message.reply_photo(poster, caption=response_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Не удалось получить данные о случайном фильме.")

@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    query = message.text[8:].strip()
    if not query:
        await message.reply("Пожалуйста, введите название фильма или сериала.")
        return

    movie_data = await fetch_movie_data(query)
    if movie_data:
        response_text = format_movie_response(movie_data)
        poster = movie_data.get("Poster", "")
        await db.save_search_history(message.from_user.id, query)

        if poster and poster != "N/A":
            await message.reply_photo(poster, caption=response_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Не удалось найти фильм. Попробуйте другой запрос.")

@dp.message(Command("clearhistory"))
async def cmd_clearhistory(message: types.Message):
    user_id = message.from_user.id
    await db.clear_search_history(user_id)
    await message.reply("Ваша история поиска была очищена.")

@dp.message(Command("quote"))
async def cmd_quote(message: types.Message):
    quotes = [
        "«Голливуд — это место, где они продадут тебе шнурок от ботинка за 20 долларов, а потом скажут, что он стоил 100 долларов.» — Уоррен Битти",
        "«Фильм — это жизнь с выключенным светом.» — Альфред Хичкок",
        "«Кино — это искусство, которое позволяет людям пережить невозможное.» — Франсуа Трюффо",
        "«Лучше бы я сделал всё как следует. Но я был слишком занят тем, чтобы снимать.» — Орсон Уэллс"
    ]
    quote = random.choice(quotes)
    await message.reply(f"Цитата: {quote}")

# Обработчик ошибок
@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    logging.error(f"Обновление {update} вызвало ошибку: {exception}")
    if hasattr(update, 'message'):
        await update.message.reply("Произошла ошибка. Попробуйте снова!")

# Основная функция для запуска бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
