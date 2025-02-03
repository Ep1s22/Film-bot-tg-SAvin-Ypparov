@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_text = """
    Вот что я умею:
    /start - Начать диалог
    /help - Показать это сообщение
    Фильмы - Показать фильмы
    Аниме - Показать аниме
    Мультсериалы - Показать мультсериалы
    Найди <название> - Найти фильм или сериал
    """
    await message.reply(help_text)
8. Итоговый код
Вот итоговый код с учетом всех улучшений:

python
Copy
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import logging

logging.basicConfig(level=logging.INFO)

API_TOKEN = 'ВАШ_ТОКЕН_ЗДЕСЬ'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Создаем папку для загрузки файлов, если она не существует
if not os.path.exists('./downloads'):
    os.makedirs('./downloads')

# Клавиатура
button1 = KeyboardButton(text='Фильмы')
button2 = KeyboardButton(text='Аниме')
button3 = KeyboardButton(text='Мультсериалы')
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(button1, button2)
keyboard.add(button3)

@dp.message_handler(lambda message: message.text.lower().startswith("найди"))
async def search_content(message: types.Message):
    query = message.text.lower().replace("найди", "").strip()
    if query:
        await message.reply(f"Ищу {query}...")
        await message.reply(f"Вот что я нашел: https://www.ivi.ru/search/?q={query}")
    else:
        await message.reply("Пожалуйста, укажите название фильма или сериала.")

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    inline_kb = InlineKeyboardMarkup()
    inline_kb.add(InlineKeyboardButton("Фильмы", url="https://www.ivi.ru/movies/dlya_vsej_semi"))
    inline_kb.add(InlineKeyboardButton("Аниме", url="https://www.kinopoisk.ru/lists/movies/top_100_horrors_by_best_horror_movies/"))
    inline_kb.add(InlineKeyboardButton("Мультсериалы", url="https://www.ivi.ru/movies/dlya_vsej_semi"))
    await message.reply("Привет! Я бот Борис наждачка. Что вы хотите посмотреть сегодня?", reply_markup=keyboard)

@dp.message_handler(lambda message: "фильм" in message.text.lower())
async def send_movies(message: types.Message):
    await message.reply("Лови: https://www.ivi.ru/movies/dlya_vsej_semi")

@dp.message_handler(lambda message: "аниме" in message.text.lower())
async def send_anime(message: types.Message):
    await message.reply("Лови: https://www.kinopoisk.ru/lists/movies/top_100_horrors_by_best_horror_movies/?utm_referrer=www.google.com")

@dp.message_handler(lambda message: "мультсериал" in message.text.lower())
async def send_cartoons(message: types.Message):
    await message.reply("Лови: https://www.ivi.ru/movies/dlya_vsej_semi")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    try:
        document_id = message.document.file_id
        file_info = await bot.get_file(document_id)
        await bot.download_file(file_info.file_path, f"./downloads/{message.document.file_name}")
        await message.reply(f"Файл {message.document.file_name} получен и сохранен.")
    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")

@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    help_text = """
    Вот что я умею:
    /start - Начать диалог
    /help - Показать это сообщение
    Фильмы - Показать фильмы
    Аниме - Показать аниме
    Мультсериалы - Показать мультсериалы
    Найди <название> - Найти фильм или сериал
    """
    await message.reply(help_text)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)











