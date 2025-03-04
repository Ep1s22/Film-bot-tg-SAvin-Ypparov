import logging
import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = '7462539798:AAFQ4WJl34YT0oNKl1c8t_nJgNgsJmOqNYg'
KINO_API_KEY = 'VV0J3CV-04DM6JJ-NB4DYGW-PC3JXWV'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class FilterState(StatesGroup):
    waiting_for_year = State()
    waiting_for_rating = State()

async def search_kinopoisk(query: str, filters: dict = None):
    url = "https://api.kinopoisk.dev/v1.3/movie"
    headers = {"X-API-KEY": KINO_API_KEY}
    params = {"name": query, "limit": 10, "sortField": "rating.kp", "sortType": "-1"}
    if filters:
        params.update(filters)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("docs"):
                        movies = []
                        for movie in data["docs"]:
                            title = movie.get("name", "Название неизвестно")
                            year = movie.get("year", "Год неизвестен")
                            rating = movie.get("rating", {}).get("kp", "Нет рейтинга")
                            description = movie.get("description", "Описание отсутствует")
                            short_desc = (description[:50] + "..." if description and len(description) > 50 else description) or "Описание отсутствует"
                            poster = movie.get("poster", {}).get("url", None)
                            watchability = movie.get("watchability", {}).get("items", [])

                            streaming_buttons = []
                            # Добавляем кнопку "Прочесть описание полностью" только если есть описание
                            if description and description != "Описание отсутствует":
                                streaming_buttons.append([InlineKeyboardButton(text="Прочесть описание полностью", callback_data=f"full_desc_{len(movies)}")])
                            # Добавляем ссылки из watchability
                            for platform in watchability or []:
                                name = platform.get("name", "Неизвестная платформа")
                                url = platform.get("url")
                                if url and url.startswith(("http://", "https://")):  # Проверяем валидность URL
                                    streaming_buttons.append([InlineKeyboardButton(text=name, url=url)])
                            
                            text = f"*{title}* ({year})\n⭐️ Рейтинг: {rating}\n📜 Описание: {short_desc}"
                            movies.append((text, poster, streaming_buttons, description or "Описание отсутствует"))
                        return movies
                    return [("Нothing found.", None, [], "")]
                logger.error(f"API Error: {response.status}, {await response.text()}")
                return [("API request error.", None, [], "")]
    except Exception as e:
        logger.error(f"Unexpected error in search_kinopoisk: {e}")
        return [("Processing request error.", None, [], "")]

def get_main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Поиск фильма 🔍")], [KeyboardButton(text="Фильтр по параметрам 📋")]], resize_keyboard=True)

def get_back_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад 🔙")]], resize_keyboard=True)

async def get_popular_movies():
    url = "https://api.kinopoisk.dev/v1.3/movie"
    headers = {"X-API-KEY": KINO_API_KEY}
    params = {"sortField": "votes.kp", "sortType": "-1", "limit": 10}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    movies = []
                    for movie in data.get("docs", []):
                        title = movie.get("name", "Название неизвестно")
                        watchability = movie.get("watchability", {}).get("items", [])
                        url = next((platform.get("url", "https://example.com") for platform in watchability if platform.get("url") and platform.get("url").startswith(("http://", "https://"))), "https://example.com")
                        movies.append({"title": title, "url": url})
                    return movies
                return [{"title": f"Фильм {i}", "url": "https://example.com"} for i in range(1, 11)]
    except Exception as e:
        logger.error(f"Error in get_popular_movies: {e}")
        return [{"title": f"Фильм {i}", "url": "https://example.com"} for i in range(1, 11)]

async def get_search_suggestions_keyboard():
    suggestions = await get_popular_movies()
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=movie["title"], url=movie["url"])] for movie in suggestions])

@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Я бот для поиска фильмов. Напишите название или используйте кнопки:", reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "Поиск фильма 🔍")
async def handle_search_button(message: Message):
    await message.answer("Выберите фильм из списка популярных:", reply_markup=await get_search_suggestions_keyboard())

@dp.message(lambda message: not message.text.startswith("/") and not message.text.startswith("Фильтр"))
async def process_movie_search(message: Message, state: FSMContext):
    query = message.text.strip()
    if query:
        movies = await search_kinopoisk(query)
        if movies is not None:
            await state.update_data(movies=movies)
            await send_movies(message, movies)
        else:
            await message.answer("Ошибка при поиске фильма.")
    else:
        await message.answer("Укажите название фильма.")

@dp.message(lambda message: message.text == "Фильтр по параметрам 📋")
async def handle_filter_button(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Год", callback_data="filter_year"), InlineKeyboardButton(text="Рейтинг", callback_data="filter_rating")]])
    await message.answer("Выберите фильтр:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('filter_'))
async def process_filter(callback_query: types.CallbackQuery, state: FSMContext):
    filter_type = callback_query.data.split('_')[1]
    if filter_type == "year":
        await show_year_buttons(callback_query.message, state)
    elif filter_type == "rating":
        await show_rating_buttons(callback_query.message, state)

async def show_year_buttons(message: Message, state: FSMContext):
    year_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=str(y), callback_data=f"year_{y}")] for y in [2023, 2020, 2015, 2010, 2005, 2000, 1995, 1990, 1985, 1980]] + [[InlineKeyboardButton(text="До 1980", callback_data="year_before_1980")]])
    await message.answer("Выберите год:", reply_markup=year_keyboard)
    await state.set_state(FilterState.waiting_for_year)

async def show_rating_buttons(message: Message, state: FSMContext):
    rating_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="7+", callback_data="rating_7")], [InlineKeyboardButton(text="8+", callback_data="rating_8")], [InlineKeyboardButton(text="9+", callback_data="rating_9")]])
    await message.answer("Выберите минимальный рейтинг:", reply_markup=rating_keyboard)
    await state.set_state(FilterState.waiting_for_rating)

@dp.callback_query(lambda c: c.data.startswith('year_'))
async def apply_year_filter(callback_query: types.CallbackQuery, state: FSMContext):
    year_data = callback_query.data.split('_')[1]
    filters = {"year": "1900-1980" if year_data == "before_1980" else year_data}
    movies = await search_kinopoisk("", filters)
    if movies is not None:
        await state.update_data(movies=movies)
        await send_movies(callback_query.message, movies)
    else:
        await callback_query.message.answer("Ошибка при применении фильтра.")
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith('rating_'))
async def apply_rating_filter(callback_query: types.CallbackQuery, state: FSMContext):
    rating = callback_query.data.split('_')[1]
    filters = {"rating.kp": f"{rating}-"}
    movies = await search_kinopoisk("", filters)
    if movies is not None:
        await state.update_data(movies=movies)
        await send_movies(callback_query.message, movies)
    else:
        await callback_query.message.answer("Ошибка при применении фильтра.")
    await state.clear()

@dp.message(FilterState.waiting_for_year)
async def handle_unexpected_input_year(message: Message, state: FSMContext):
    await message.answer("Выберите год из вариантов или введите корректный год (например, 2020).")

@dp.message(FilterState.waiting_for_rating)
async def handle_unexpected_input_rating(message: Message, state: FSMContext):
    await message.answer("Выберите рейтинг из вариантов или введите корректный рейтинг (например, 7.5).")

async def send_movies(message: Message, movies: list, page: int = 0):
    if not movies:
        await message.answer("Список фильмов пуст.")
        return
    
    movies_per_page = 3
    start = page * movies_per_page
    end = start + movies_per_page
    movies_to_send = movies[start:end]

    for text, poster, streaming_buttons, full_desc in movies_to_send:
        keyboard = InlineKeyboardMarkup(inline_keyboard=streaming_buttons) if streaming_buttons else None
        if poster:
            await message.answer_photo(photo=poster, caption=text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

    if len(movies) > end:
        navigation_keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Следующие ➡️", callback_data=f"next_page_{page + 1}")]])
        await message.answer("Показать ещё?", reply_markup=navigation_keyboard)

@dp.callback_query(lambda c: c.data.startswith('next_page_'))
async def handle_next_page(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split('_')[2])
    data = await state.get_data()
    movies = data.get("movies", [])
    if movies:
        await send_movies(callback_query.message, movies, page)
    else:
        await callback_query.message.answer("Ошибка: список фильмов потерян. Начните поиск заново.")

@dp.callback_query(lambda c: c.data.startswith('full_desc_'))
async def show_full_description(callback_query: types.CallbackQuery, state: FSMContext):
    index = int(callback_query.data.split('_')[2])
    data = await state.get_data()
    movies = data.get("movies", [])
    if movies and 0 <= index < len(movies):
        full_desc = movies[index][3]
        await callback_query.message.answer(f"📜 Полное описание:\n{full_desc}", parse_mode="Markdown")
    else:
        await callback_query.message.answer("Ошибка: описание не найдено.")

async def main():
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
if __name__ == "__main__":
    asyncio.run(main())
