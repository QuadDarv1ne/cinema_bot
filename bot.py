import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiohttp import ClientSession
from dotenv import load_dotenv
from db import Database

# Загрузка переменных окружения
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация базы данных
db = Database()

# Определение состояний
class BotStates(StatesGroup):
    waiting_for_movie = State()

# Вспомогательная функция для получения данных о фильме
async def fetch_movie_data(query: str) -> dict:
    async with ClientSession() as session:
        async with session.get(f'http://www.omdbapi.com/?t={query}&apikey={OMDB_API_KEY}') as response:
            return await response.json()

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
        history_text = "\n".join([f"{i+1}. {query}" for i, query in enumerate(history)])
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
    query = message.text
    movie_data = await fetch_movie_data(query)
    
    if movie_data.get("Response") == "True":
        title = movie_data.get("Title", "Неизвестно")
        year = movie_data.get("Year", "Неизвестно")
        rating = movie_data.get("imdbRating", "Нет рейтинга")
        poster = movie_data.get("Poster", "")
        plot = movie_data.get("Plot", "Описание отсутствует")
        link = f"https://www.imdb.com/title/{movie_data.get('imdbID', '')}"

        # Сохранение истории поиска
        db.save_search_history(message.from_user.id, query)
        
        response_text = (
            f"🎬 *{title}* ({year})\n\n"
            f"📊 Рейтинг IMDb: {rating}\n\n"
            f"📜 Сюжет: {plot}\n\n"
            f"🔗 [Ссылка на IMDb]({link})"
        )

        if poster and poster != "N/A":
            await message.reply_photo(poster, caption=response_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply(response_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Я не смог найти информацию об этом фильме. Пожалуйста, попробуйте другой запрос.")

# Обработчик ошибок
@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    logging.error(f"Обновление {update} вызвало ошибку {exception}")
    if update.message:
        await update.message.reply("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.")

# Основная функция для запуска бота
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
