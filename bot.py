import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

API_TOKEN = '7462539798:AAFQ4WJl34YT0oNKl1c8t_nJgNgsJmOqNYg'
KINO_API_KEY = 'VV0J3CV-04DM6JJ-NB4DYGW-PC3JXWV'  # Ваш API-ключ

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
class FilterState(StatesGroup):
    waiting_for_genre = State()
    waiting_for_year = State()
    waiting_for_rating = State()


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
                if data.get("docs"):
                    movies = []
                    for movie in data["docs"]:
                        title = movie.get("name", "Название неизвестно")
                        year = movie.get("year", "Год неизвестен")
                        rating = movie.get("rating", {}).get("kp", "Нет рейтинга")
                        description = movie.get("description", "Описание отсутствует")
                        poster = movie.get("poster", {}).get("url", None)
                        
                        text = (f"*{title}* ({year})\n"
                                f"⭐️ Рейтинг: {rating}\n"
                                f"📜 Описание: {description}")
                        movies.append((text, poster))
                    
                    return movies
                else:
                    return [("Ничего не найдено.", None)]
            else:
                return [("Ошибка при запросе к API.", None)]

# Команда: /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer(
        "Привет! Я бот для поиска фильмов, сериалов, мультфильмов и аниме.\n"
        "Используй команды:\n"
        "/search <название фильма> - поиск по названию\n"
        "/filter - поиск с фильтрами"
    )

@dp.message(Command("search"))
async def search_movies(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Пожалуйста, укажите название фильма. Например: /search Интерстеллар", parse_mode="Markdown")
        return

    movies = await search_kinopoisk(args[1])

    for text, poster in movies:
        if poster:
            await message.answer_photo(photo=poster, caption=text, parse_mode="Markdown")
        else:
            await message.answer(text, parse_mode="Markdown")


@dp.message(Command("filter"))
async def filter_movies(message: Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="Жанр", callback_data="filter_genre"),
        InlineKeyboardButton(text="Год", callback_data="filter_year"),
        InlineKeyboardButton(text="Рейтинг", callback_data="filter_rating")
    )
    await message.answer("Выберите фильтр:", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('filter_'))
async def process_filter(callback_query: types.CallbackQuery, state: FSMContext):
    filter_type = callback_query.data.split('_')[1]
    
    if filter_type == "genre":
        await callback_query.message.answer("Введите жанр (например, комедия, боевик):")
        await state.set_state(FilterState.waiting_for_genre)
    elif filter_type == "year":
        await callback_query.message.answer("Введите год (например, 2020):")
        await state.set_state(FilterState.waiting_for_year)
    elif filter_type == "rating":
        await callback_query.message.answer("Введите минимальный рейтинг (например, 7):")
        await state.set_state(FilterState.waiting_for_rating)

@dp.message(FilterState.waiting_for_genre)
async def apply_genre_filter(message: Message, state: FSMContext):
    genre = message.text.strip()
    filters = {"genres.name": genre}
    await process_filters(message, filters)
    await state.clear()

@dp.message(FilterState.waiting_for_year)
async def apply_year_filter(message: Message, state: FSMContext):
    year = message.text.strip()
    if year.isdigit() and len(year) == 4:
        filters = {"year": year}
        await process_filters(message, filters)
    else:
        await message.answer("Пожалуйста, введите корректный год (например, 2020).")
    await state.clear()

@dp.message(FilterState.waiting_for_rating)
async def apply_rating_filter(message: Message, state: FSMContext):
    rating = message.text.strip()
    if rating.isdigit():
        filters = {"rating.kp": rating}
        await process_filters(message, filters)
    else:
        await message.answer("Пожалуйста, введите корректный рейтинг (например, 7).")
    await state.clear()

async def process_filters(message: Message, filters: dict):
    movies = await search_kinopoisk("", filters)
    for text, poster in movies:
        if poster:
            await message.answer_photo(photo=poster, caption=text, parse_mode="Markdown")
        else:
            await message.answer(text, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())











