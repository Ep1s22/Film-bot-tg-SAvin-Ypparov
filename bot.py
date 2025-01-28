import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware 
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '7462539798:AAFQ4WJl34YT0oNKl1c8t_nJgNgsJmOqNYg'

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
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    button1 = InlineKeyboardButton("Хорор", callback_data="button1")
    button2 = InlineKeyboardButton("Ромаентика", callback_data="button2")
    keyboard.add(button1, button2)
    await message.answer("Хорор:", reply_markup=keyboard)
@dp.callback_query_handler(lambda c: c.data)
async def process_callback(callback_query: types.CallbackQuery):
    if callback_query.data == "button1":
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Лови: https://www.ivi.ru/movies/dlya_vsej_semi")
    elif callback_query.data == "button2":
        await bot.answer_callback_query(callback_query.id)
        await bot.send_message(callback_query.from_user.id, "Лови: https://www.kinopoisk.ru/lists/movies/top_100_horrors_by_best_horror_movies/?utm_referrer=www.google.com")

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

@dp.message_handler(lambda message: message.text.lower() == "нормально")
async def greet_user(message: types.Message):
    await message.reply("я тоже хорошо, а вы любите фильмы?")











