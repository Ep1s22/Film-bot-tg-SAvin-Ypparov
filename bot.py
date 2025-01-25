
API_TOKEN = '7462539798:AAFQ4WJl34YT0oNKl1c8t_nJgNgsJmOqNYg'

import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor 
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())
def start(message):
 bot.send_message(message.chat.id, 'выбирай ')
 markup= types.ReplyKeyboardMarkup()
 btn1 = types.KeyboardButton('кнопка')
 btn2 = types.KeyboardButton('кнопка')
 markup.add(btn1, btn2)
 bot.send_message(message.chat.id, 'выбирай', reply_markup=markup)
# клвавиатура ваааааа осталось придумать как стучать на сайты аааа 
ch = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Фильмы')],
    [KeyboardButton(text='Аниме')]
    [KeyboardButton(text='Мультфильмы')]
])

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    print(message)
    document_id = message.document.file_id
    file_info = await bot.get_file(document_id)
    await bot.download_file(file_info.file_path, f"./downloads/{message.document.file_name}")
    await bot.send_message(message.chat.id, f"Файл {message.document.file_name} получен и сохранен.")

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, "Привет! Я бот Борис наждачка. как ваши дела. Что вы хотите посмотреть сегодня ")

@dp.message_handler(commands=['Для_все_семьи'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, "https://www.ivi.ru/movies/dlya_vsej_semi")

@dp.message_handler(lambda message: message.text.lower() == "привет")
async def greet_user(message: types.Message):
    await message.reply("Привет! Как дела?")

@dp.message_handler(lambda message: message.text.lower() == "нормально")
async def greet_user(message: types.Message):
    await message.reply("я тоже хорошо, а вы любите фильмы?")

@dp.message_handler(commands=['famali'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, "Лови: https://www.ivi.ru/movies/dlya_vsej_semi")
@dp.message_handler(commands=['horor'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, "Лови: https://www.kinopoisk.ru/lists/movies/top_100_horrors_by_best_horror_movies/?utm_referrer=www.google.com")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)











