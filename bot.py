import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токены для бота и API
API_TOKEN = '7462539798:AAFQ4WJl34YT0oNKl1c8t_nJgNgsJmOqNYg'
KINO_API_KEY = 'VV0J3CV-04DM6JJ-NB4DYGW-PC3JXWV'  # Ваш API-ключ

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Состояния для FSM (оставляем только для года и рейтинга)
class FilterState(StatesGroup):
    waiting_for_year = State()
    waiting_for_rating = State()

# Функция для поиска фильмов через API Кинопоиска
async def search_kinopoisk(query: str, filters: dict = None):
    url = "https://api.kinopoisk.dev/v1.3/movie"
    headers = {"X-API-KEY": KINO_API_KEY}
    params = {"name": query, "limit": 10, "sortField": "rating.kp", "sortType": "-1"}  # Ограничиваем 10 фильмами
    
    if filters:
        params.update(filters)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                print(f"API Response: {data}")  # Логируем ответ API
                if data.get("docs"):
                    movies = []
                    for movie in data["docs"]:
                        title = movie.get("name", "Название неизвестно")
                        year = movie.get("year", "Год неизвестен")
                        rating = movie.get("rating", {}).get("kp", "Нет рейтинга")
                        description = movie.get("description", "Описание отсутствует")
                        poster = movie.get("poster", {}).get("url", None)
                        streamings = movie.get("streamings", [])  # Получаем список платформ

                        # Создаем кнопки для платформ, если они существуют
                        streaming_buttons = []
                        if streamings:
                            for platform in streamings:
                                name = platform.get("name", "Неизвестная платформа")
                                url = platform.get("url", "#")
                                if url and name:  # Проверяем, что есть имя и ссылка
                                    streaming_buttons.append([InlineKeyboardButton(text=name, url=url)])
                        
                        # Генерируем текст сообщения
                        text = (f"*{title}* ({year})\n"
                                f"⭐️ Рейтинг: {rating}\n"
                                f"📜 Описание: {description}")
                        
                        # Добавляем фильм в список с кнопками
                        movies.append((text, poster, streaming_buttons))
                    
                    return movies
                else:
                    print(f"No results found for query: {query}, filters: {filters}")
                    return [("Ничего не найдено.", None, [])]
            else:
                print(f"API Error: {response.status}, {await response.text()}")
                return [("Ошибка при запросе к API.", None, [])]

# Создание клавиатуры с кнопками для команд
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Поиск фильма 🔍")],
            [KeyboardButton(text="Фильтр по параметрам 📋")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Предложенные фильмы для быстрого поиска
def get_search_suggestions():
    suggestions = [
        "Интерстеллар",
        "Матрица",
        "Властелин колец",
        "Зеленая миля",
        "Титаник",
        "Джокер",
        "Аватар",
        "Пираты Карибского моря",
        "Гарри Поттер",
        "Веном"
    ]
    return suggestions

# Создание инлайн-клавиатуры с предложенными фильмами
def get_search_suggestions_keyboard():
    suggestions = get_search_suggestions()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=film, callback_data=f"search_{film}")] for film in suggestions
    ])
    return keyboard

# Команда: /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer(
        "Привет! Я бот для поиска фильмов, сериалов, мультфильмов и аниме.\n"
        "Вы можете просто написать название фильма, и я найду его для вас!\n"
        "Или используйте кнопки ниже для взаимодействия:",
        reply_markup=get_main_keyboard()
    )

# Обработка кнопки "Поиск фильма"
@dp.message(lambda message: message.text == "Поиск фильма 🔍")
async def handle_search_button(message: Message):
    await message.answer(
        "Выберите фильм из предложенных вариантов или напишите название самостоятельно:",
        reply_markup=get_search_suggestions_keyboard()
    )

# Обработка выбора фильма из предложенных вариантов
@dp.callback_query(lambda c: c.data.startswith('search_'))
async def process_search_suggestion(callback_query: types.CallbackQuery):
    query = callback_query.data.split('_')[1]
    movies = await search_kinopoisk(query)
    for text, poster, streaming_buttons in movies:
        # Создаем клавиатуру с кнопками для платформ
        keyboard = InlineKeyboardMarkup(inline_keyboard=streaming_buttons) if streaming_buttons else None
        
        if poster:
            await callback_query.message.answer_photo(photo=poster, caption=text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await callback_query.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

# Обработка текстового ввода (поиск по названию фильма)
@dp.message(lambda message: not message.text.startswith("/") and not message.text.startswith("Фильтр"))
async def process_movie_search(message: Message):
    query = message.text.strip()
    if query:
        movies = await search_kinopoisk(query)
        for text, poster, streaming_buttons in movies:
            # Создаем клавиатуру с кнопками для платформ
            keyboard = InlineKeyboardMarkup(inline_keyboard=streaming_buttons) if streaming_buttons else None
            
            if poster:
                await message.answer_photo(photo=poster, caption=text, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message.answer("Пожалуйста, укажите название фильма.")

# Обработка кнопки "Фильтр по параметрам"
@dp.message(lambda message: message.text == "Фильтр по параметрам 📋")
async def handle_filter_button(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Год", callback_data="filter_year"),
            InlineKeyboardButton(text="Рейтинг", callback_data="filter_rating")
        ]
    ])
    await message.answer("Выберите фильтр:", reply_markup=keyboard)

# Обработка callback-запросов для фильтров
@dp.callback_query(lambda c: c.data.startswith('filter_'))
async def process_filter(callback_query: types.CallbackQuery, state: FSMContext):
    filter_type = callback_query.data.split('_')[1]
    
    if filter_type == "year":
        await show_year_buttons(callback_query.message, state)
    elif filter_type == "rating":
        await show_rating_buttons(callback_query.message, state)

# Показать кнопки с годами
async def show_year_buttons(message: Message, state: FSMContext):
    year_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="2023", callback_data="year_2023")],
        [InlineKeyboardButton(text="2020", callback_data="year_2020")],
        [InlineKeyboardButton(text="2015", callback_data="year_2015")],
        [InlineKeyboardButton(text="2010", callback_data="year_2010")],
        [InlineKeyboardButton(text="2005", callback_data="year_2005")],
        [InlineKeyboardButton(text="2000", callback_data="year_2000")],
        [InlineKeyboardButton(text="1995", callback_data="year_1995")],
        [InlineKeyboardButton(text="1990", callback_data="year_1990")],
        [InlineKeyboardButton(text="1985", callback_data="year_1985")],
        [InlineKeyboardButton(text="1980", callback_data="year_1980")],
        [InlineKeyboardButton(text="До 1980", callback_data="year_before_1980")]
    ])
    await message.answer("Выберите год:", reply_markup=year_keyboard)
    await state.set_state(FilterState.waiting_for_year)

# Показать кнопки с рейтингами
async def show_rating_buttons(message: Message, state: FSMContext):
    rating_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7+", callback_data="rating_7")],
        [InlineKeyboardButton(text="8+", callback_data="rating_8")],
        [InlineKeyboardButton(text="9+", callback_data="rating_9")]
    ])
    await message.answer("Выберите минимальный рейтинг:", reply_markup=rating_keyboard)
    await state.set_state(FilterState.waiting_for_rating)

# Обработка выбора года
@dp.callback_query(lambda c: c.data.startswith('year_'))
async def apply_year_filter(callback_query: types.CallbackQuery, state: FSMContext):
    year_data = callback_query.data.split('_')[1]
    
    if year_data == "before_1980":
        filters = {"year": "1900-1980"}
    else:
        filters = {"year": year_data}
    
    await process_filters(callback_query.message, filters)
    await state.clear()

# Обработка выбора рейтинга
@dp.callback_query(lambda c: c.data.startswith('rating_'))
async def apply_rating_filter(callback_query: types.CallbackQuery, state: FSMContext):
    rating = callback_query.data.split('_')[1]
    filters = {"rating.kp": f"{rating}-"}
    await process_filters(callback_query.message, filters)
    await state.clear()

# Общая функция для обработки фильтров
async def process_filters(message: Message, filters: dict):
    movies = await search_kinopoisk("", filters)
    for text, poster, streaming_buttons in movies:
        # Создаем клавиатуру с кнопками для платформ
        keyboard = InlineKeyboardMarkup(inline_keyboard=streaming_buttons) if streaming_buttons else None
        
        if poster:
            await message.answer_photo(photo=poster, caption=text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

# Основная функция
async def main():
    await dp.start_polling(bot)

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())











