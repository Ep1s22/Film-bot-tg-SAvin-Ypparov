import logging
import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = '7462539798:AAFQ4WJl34YT0oNKl1c8t_nJgNgsJmOqNYg'
KINO_API_KEY = 'VV0J3CV-04DM6JJ-NB4DYGW-PC3JXWV'  # Ваш API-ключ

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# фсм
class FilterState(StatesGroup):
    waiting_for_year = State()
    waiting_for_rating = State()

# кинопоиск функ
async def search_kinopoisk(query: str, filters: dict = None):
    url = "https://api.kinopoisk.dev/v1.3/movie"
    headers = {"X-API-KEY": KINO_API_KEY}
    params = {"name": query, "limit": 10, "sortField": "rating.kp", "sortType": "-1"}  # Ограничиваем 10 фильмами
    
    if filters:
        params.update(filters)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"API Response: {json.dumps(data, ensure_ascii=False, indent=4)}")
                    
                    if data.get("docs"):
                        movies = []
                        for movie in data["docs"]:
                            title = movie.get("name", "Название неизвестно")
                            year = movie.get("year", "Год неизвестен")
                            rating = movie.get("rating", {}).get("kp", "Нет рейтинга")
                            description = movie.get("description", "Описание отсутствует")
                            poster = movie.get("poster", {}).get("url", None)
                            watchability = movie.get("watchability", {}).get("items", [])

                            streaming_buttons = []
                            for platform in watchability:
                                name = platform.get("name", "Неизвестная платформа")
                                url = platform.get("url", "#")
                                if url and name:
                                    streaming_buttons.append([InlineKeyboardButton(text=name, url=url)])
                            
                            text = (f"*{title}* ({year})\n"
                                    f"⭐️ Рейтинг: {rating}\n"
                                    f"📜 Описание: {description}")
                            
                            movies.append((text, poster, streaming_buttons))
                        
                        return movies
                    else:
                        logger.warning(f"No results found for query: {query}, filters: {filters}")
                        return [("Ничего не найдено.", None, [])]
                else:
                    logger.error(f"API Error: {response.status}, {await response.text()}")
                    return [("Ошибка при запросе к API.", None, [])]
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return [("Произошла ошибка при обработке запроса.", None, [])]

# осн команды
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Поиск фильма 🔍")],
            [KeyboardButton(text="Фильтр по параметрам 📋")]
        ],
        resize_keyboard=True
    )
    return keyboard

# клава еще (назад)
def get_back_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад 🔙")]],
        resize_keyboard=True
    )
    return keyboard

# фильмы на предложке
async def get_popular_movies():
    url = "https://api.kinopoisk.dev/v1.3/movie"
    headers = {"X-API-KEY": KINO_API_KEY}
    params = {"sortField": "votes.kp", "sortType": "-1", "limit": 10}  # Топ-10 по количеству голосов
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return [movie.get("name", "Неизвестно") for movie in data.get("docs", [])]
            else:
                return ["Интерстеллар", "Матрица", "Властелин колец"]  # Запасной список

# кнопки с фильмами на предложке
async def get_search_suggestions_keyboard():
    suggestions = await get_popular_movies()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=film, callback_data=f"search_{film}")] for film in suggestions
    ])
    return keyboard

@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer(
        "Привет! Я бот для поиска фильмов, сериалов, мультфильмов и аниме.\n"
        "Вы можете просто написать название фильма, и я найду его для вас!\n"
        "Или используйте кнопки ниже для взаимодействия:",
        reply_markup=get_main_keyboard()
    )

# поиск фильма САМОЕ ПЕРВНОЕ ЧТО НАПИСАЛ НЕ РАБОТАЛО 3 ДНЯ 
@dp.message(lambda message: message.text == "Поиск фильма 🔍")
async def handle_search_button(message: Message):
    await message.answer(
        "Выберите фильм из предложенных вариантов или напишите название самостоятельно:",
        reply_markup=await get_search_suggestions_keyboard()
    )

@dp.callback_query(lambda c: c.data.startswith('search_'))
async def process_search_suggestion(callback_query: types.CallbackQuery):
    query = callback_query.data.split('_')[1]
    movies = await search_kinopoisk(query)
    await send_movies(callback_query.message, movies)

# обрабатывает что было щакинуто в поиск
@dp.message(lambda message: not message.text.startswith("/") and not message.text.startswith("Фильтр"))
async def process_movie_search(message: Message):
    query = message.text.strip()
    if query:
        movies = await search_kinopoisk(query)
        await send_movies(message, movies)
    else:
        await message.answer("Пожалуйста, укажите название фильма.")

# обработка двух фильтров должно было быть 3 но 3 перестал работать ((
@dp.message(lambda message: message.text == "Фильтр по параметрам 📋")
async def handle_filter_button(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Год", callback_data="filter_year"),
            InlineKeyboardButton(text="Рейтинг", callback_data="filter_rating")
        ]
    ])
    await message.answer("Выберите фильтр:", reply_markup=keyboard)

# обратные запросы кинопоиску
@dp.callback_query(lambda c: c.data.startswith('filter_'))
async def process_filter(callback_query: types.CallbackQuery, state: FSMContext):
    filter_type = callback_query.data.split('_')[1]
    
    if filter_type == "year":
        await show_year_buttons(callback_query.message, state)
    elif filter_type == "rating":
        await show_rating_buttons(callback_query.message, state)

# кнопочки с годами 
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

# кнопочки с рейтингом
async def show_rating_buttons(message: Message, state: FSMContext):
    rating_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7+", callback_data="rating_7")],
        [InlineKeyboardButton(text="8+", callback_data="rating_8")],
        [InlineKeyboardButton(text="9+", callback_data="rating_9")]
    ])
    await message.answer("Выберите минимальный рейтинг:", reply_markup=rating_keyboard)
    await state.set_state(FilterState.waiting_for_rating)

@dp.callback_query(lambda c: c.data.startswith('year_'))
async def apply_year_filter(callback_query: types.CallbackQuery, state: FSMContext):
    year_data = callback_query.data.split('_')[1]
    
    if year_data == "before_1980":
        filters = {"year": "1900-1980"}
    else:
        filters = {"year": year_data}
    
    await process_filters(callback_query.message, filters)
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith('rating_'))
async def apply_rating_filter(callback_query: types.CallbackQuery, state: FSMContext):
    rating = callback_query.data.split('_')[1]
    filters = {"rating.kp": f"{rating}-"}
    await process_filters(callback_query.message, filters)
    await state.clear()

# если введен в поиск не учитаный вариант года
@dp.message(FilterState.waiting_for_year)
async def handle_unexpected_input_year(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, выберите год из предложенных вариантов или введите корректный год (например, 2020).")

# если введен в поиск не учитаный вариант рейта
@dp.message(FilterState.waiting_for_rating)
async def handle_unexpected_input_rating(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, выберите рейтинг из предложенных вариантов или введите корректный рейтинг (например, 7.5).")

async def process_filters(message: Message, filters: dict):
    movies = await search_kinopoisk("", filters)
    await send_movies(message, movies)

# что бы не все сразу
async def send_movies(message: Message, movies: list, page: int = 0):
    movies_per_page = 3  # Количество фильмов на одной странице
    start = page * movies_per_page
    end = start + movies_per_page
    movies_to_send = movies[start:end]

    for text, poster, streaming_buttons in movies_to_send:
        keyboard = InlineKeyboardMarkup(inline_keyboard=streaming_buttons) if streaming_buttons else None
        
        if poster:
            await message.answer_photo(photo=poster, caption=text, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

    # кнопочка для навигации 
    if len(movies) > end:
        navigation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Следующие ➡️", callback_data=f"next_page_{page + 1}")]
        ])
        await message.answer("Показать ещё?", reply_markup=navigation_keyboard)

@dp.callback_query(lambda c: c.data.startswith('next_page_'))
async def handle_next_page(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split('_')[2])
    movies = await search_kinopoisk("")  # Здесь нужно передать текущий запрос
    await send_movies(callback_query.message, movies, page)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
