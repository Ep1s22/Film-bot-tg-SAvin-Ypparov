import logging
import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import List, Tuple, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_TOKEN = '7462539798:AAFQ4WJl34YT0oNKl1c8t_nJgNgsJmOqNYg'
KINO_API_KEY = 'VV0J3CV-04DM6JJ-NB4DYGW-PC3JXWV'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class FilterState(StatesGroup):
    waiting_for_year = State()
    waiting_for_rating = State()
    waiting_for_genre = State()
    waiting_for_actor = State()

async def search_kinopoisk(query: str, filters: str = None) -> List[Tuple[str, str, List[List[InlineKeyboardButton]], str, Dict]]:
    url = "https://api.kinopoisk.dev/v1.3/movie"
    headers = {"X-API-KEY": KINO_API_KEY}
    params = {"name": query.strip(), "limit": 10, "sortField": "rating.kp", "sortType": "-1"}
    if filters:
        try:
            params.update(json.loads(filters))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid filter JSON: {e}")
            return [("Invalid filter format.", None, [], "", {})]

    logger.info(f"Sending request to API with query: '{query}', filters: '{filters}'")
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=100)) as session:
        try:
            async with session.get(url, headers=headers, params=params) as response:
                logger.info(f"API response status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    docs = data.get("docs", [])
                    logger.info(f"Found {len(docs)} movies for query '{query}' with filters '{filters}'")
                    if not docs:
                        return [("Фильм не найден. Проверьте название или попробуйте другое.", None, [], "", {})]
                    
                    movies = []
                    for i, movie in enumerate(docs):
                        description = movie.get('description')
                        if description is None:
                            description = 'Описание отсутствует'
                        short_desc = description[:50] + '...' if len(description) > 50 else description
                        
                        text = (
                            f"*{movie.get('name', 'Название неизвестно')}* ({movie.get('year', 'Год неизвестен')})\n"
                            f"⭐️ Рейтинг: {movie.get('rating', {}).get('kp', 'Нет рейтинга')}\n"
                            f"📜 Описание: {short_desc}"
                        )
                        poster = movie.get("poster", {}).get("url")
                        watchability_items = movie.get("watchability", {}).get("items", [])
                        streaming_buttons = [
                            [InlineKeyboardButton(text=plat.get("name"), url=plat.get("url"))]
                            for plat in watchability_items[:3]
                            if plat.get("url", "").startswith(("http://", "https://"))
                        ]
                        buttons = (
                            [[InlineKeyboardButton(text="Полное описание", callback_data=f"full_desc_{i}")]]
                            if movie.get("description") is not None else []
                        ) + streaming_buttons + [
                            [InlineKeyboardButton(text="Похожие фильмы 🔍", callback_data=f"similar_{i}")]
                        ]
                        movies.append((text, poster, buttons, description, movie))
                    return movies
                logger.error(f"API Error: {response.status}, {await response.text()}")
                return [("Ошибка API. Проверьте ключ или лимит запросов.", None, [], "", {})]
        except Exception as e:
            logger.error(f"Search error: {e}")
            return [("Ошибка обработки запроса. Попробуйте позже.", None, [], "", {})]

def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Поиск фильма 🔍"), KeyboardButton(text="Фильтр по параметрам 📋")],
            [KeyboardButton(text="Очистить чат 🧹")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад 🔙")]], resize_keyboard=True)

async def get_popular_movies() -> List[Dict[str, str]]:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=100)) as session:
        try:
            async with session.get(
                "https://api.kinopoisk.dev/v1.3/movie",
                headers={"X-API-KEY": KINO_API_KEY},
                params={"sortField": "votes.kp", "sortType": "-1", "limit": 10}
            ) as response:
                if response.status == 200:
                    return [
                        {
                            "title": movie.get("name", f"Фильм {i}"),
                            "url": next(
                                (plat.get("url", "https://example.com") 
                                 for plat in movie.get("watchability", {}).get("items", [])[:3]
                                 if plat.get("url", "").startswith(("http://", "https://"))),
                                "https://example.com"
                            )
                        }
                        for i, movie in enumerate((await response.json()).get("docs", []), 1)
                    ]
                return [{"title": f"Фильм {i}", "url": "https://example.com"} for i in range(1, 11)]
        except Exception as e:
            logger.error(f"Popular movies error: {e}")
            return [{"title": f"Фильм {i}", "url": "https://example.com"} for i in range(1, 11)]

async def get_search_suggestions_keyboard() -> InlineKeyboardMarkup:
    suggestions = await get_popular_movies()
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=m["title"], url=m["url"])] for m in suggestions]
    )

@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Я бот для поиска фильмов:", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "Поиск фильма 🔍")
async def handle_search_button(message: Message):
    await message.answer("Выберите популярный фильм или введите название:", reply_markup=await get_search_suggestions_keyboard())

@dp.message(lambda m: m.text == "Очистить чат 🧹")
async def handle_clear_chat(message: Message):
    chat_id = message.chat.id
    message_id = message.message_id
    try:
        for i in range(message_id, message_id - 100, -1):
            try:
                await bot.delete_message(chat_id=chat_id, message_id=i)
            except Exception:
                continue
        await message.answer("Чат очищен!", reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Error clearing chat: {e}")
        await message.answer("Ошибка при очистке чата.", reply_markup=get_main_keyboard())

@dp.message(lambda m: not m.text.startswith(("/", "Фильтр", "Назад")))
async def process_movie_search(message: Message, state: FSMContext):
    if not message.text.strip():
        await message.answer("Пожалуйста, введите название фильма.")
        return
    movies = await search_kinopoisk(message.text)
    if movies and movies[0][0] != "Processing request error.":
        await state.update_data(movies=movies)
        await send_movies(message, movies)
    else:
        await message.answer("Ошибка при поиске фильма. Проверьте подключение или попробуйте позже.")

@dp.message(lambda m: m.text == "Фильтр по параметрам 📋")
async def handle_filter_button(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Год", callback_data="filter_year")],
        [InlineKeyboardButton(text="Рейтинг", callback_data="filter_rating")],
        [InlineKeyboardButton(text="Жанр", callback_data="filter_genre")],
        [InlineKeyboardButton(text="Актёр", callback_data="filter_actor")]
    ])
    await message.answer("Выберите фильтр:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith('filter_'))
async def process_filter(callback_query: types.CallbackQuery, state: FSMContext):
    filter_type = callback_query.data.split('_')[1]
    handlers = {
        "year": show_year_buttons,
        "rating": show_rating_buttons,
        "genre": show_genre_buttons,
        "actor": show_actor_buttons
    }
    await handlers[filter_type](callback_query.message, state)

@dp.callback_query(lambda c: c.data.startswith('similar_'))
async def show_similar_movies(callback_query: types.CallbackQuery, state: FSMContext):
    index = int(callback_query.data.split('_')[1])
    data = await state.get_data()
    movies = data.get("movies", [])
    if 0 <= index < len(movies):
        selected_movie = movies[index][4]  # Полные данные фильма
        genres = selected_movie.get("genres", [])
        persons = selected_movie.get("persons", [])
        
        # Логируем данные фильма для отладки
        logger.info(f"Selected movie data: genres={genres}, persons={persons}")
        
        # Извлекаем жанр и актёра
        genre = genres[0]["name"] if genres else None
        actor = next((p["name"] for p in persons if p.get("enProfession") == "actor"), None) if persons else None
        
        # Если нет ни жанра, ни актёра, сообщаем об этом
        if not genre and not actor:
            await callback_query.message.answer("Недостаточно данных для поиска похожих фильмов (нет жанра или актёров).")
            await callback_query.answer()
            return
        
        # Формируем фильтр: сначала только по жанру, если есть
        filters = {}
        if genre:
            filters["genres.name"] = genre
        elif actor:  # Если жанра нет, используем актёра
            filters["persons.name"] = actor
        
        similar_filters = json.dumps(filters)
        logger.info(f"Similar movies filter: {similar_filters}")
        similar_movies = await search_kinopoisk("", similar_filters)
        
        if similar_movies and similar_movies[0][0] != "Processing request error.":
            if similar_movies[0][0] != "Фильм не найден. Проверьте название или попробуйте другое.":
                await state.update_data(movies=similar_movies)
                await send_movies(callback_query.message, similar_movies)
            else:
                await callback_query.message.answer(f"Похожие фильмы не найдены для жанра '{genre}' или актёра '{actor}'.")
        else:
            await callback_query.message.answer("Ошибка при поиске похожих фильмов.")
    else:
        await callback_query.message.answer("Ошибка: исходный фильм не найден в текущем состоянии.")
    await callback_query.answer()

async def show_year_buttons(message: Message, state: FSMContext):
    years = [2023, 2020, 2015, 2010, 2000]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(y), callback_data=f"year_{y}")] for y in years
    ] + [[InlineKeyboardButton(text="До 2000", callback_data="year_before_2000")]])
    await message.answer("Выберите год:", reply_markup=keyboard)
    await state.set_state(FilterState.waiting_for_year)

async def show_rating_buttons(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{r}+", callback_data=f"rating_{r}")] for r in [7, 8, 9]
    ])
    await message.answer("Выберите минимальный рейтинг:", reply_markup=keyboard)
    await state.set_state(FilterState.waiting_for_rating)

async def show_genre_buttons(message: Message, state: FSMContext):
    genres = [
        "драма", "комедия", "боевик", "фантастика", "ужасы",
        "триллер", "мелодрама", "приключения", "детектив", "фэнтези",
        "анимация", "биография", "исторический", "криминал", "вестерн"
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=g, callback_data=f"genre_{g}")] for g in genres
    ])
    await message.answer("Выберите жанр:", reply_markup=keyboard)
    await state.set_state(FilterState.waiting_for_genre)

async def show_actor_buttons(message: Message, state: FSMContext):
    await message.answer("Введите имя актёра:", reply_markup=get_back_keyboard())
    await state.set_state(FilterState.waiting_for_actor)

@dp.callback_query(lambda c: c.data.startswith(('year_', 'rating_', 'genre_')))
async def apply_filter(callback_query: types.CallbackQuery, state: FSMContext):
    filter_type, value = callback_query.data.split('_', 1)
    filters = {
        "year": json.dumps({"year": "1900-2000" if value == "before_2000" else value}),
        "rating": json.dumps({"rating.kp": f"{value}-"}),
        "genre": json.dumps({"genres.name": value})
    }
    movies = await search_kinopoisk("", filters[filter_type])
    if movies and movies[0][0] != "Processing request error.":
        await state.update_data(movies=movies)
        await send_movies(callback_query.message, movies)
    else:
        await callback_query.message.answer("Ошибка при применении фильтра.")
    await state.clear()

@dp.message(FilterState.waiting_for_actor)
async def apply_actor_filter(message: Message, state: FSMContext):
    if message.text == "Назад 🔙":
        await message.answer("Выберите действие:", reply_markup=get_main_keyboard())
        await state.clear()
        return
    movies = await search_kinopoisk("", json.dumps({"persons.name": message.text.strip()}))
    if movies and movies[0][0] != "Processing request error.":
        await state.update_data(movies=movies)
        await send_movies(message, movies)
    else:
        await message.answer("Ошибка при поиске по актёру.")
    await state.clear()

async def send_movies(message: Message, movies: List[Tuple[str, str, List[List[InlineKeyboardButton]], str, Dict]], page: int = 0):
    if not movies or not isinstance(movies, list):
        await message.answer("Фильмы не найдены или данные некорректны.")
        logger.error(f"Invalid movies data: {movies}")
        return
    
    movies_per_page = 3
    start = page * movies_per_page
    end = min(start + movies_per_page, len(movies))
    
    for i, (text, poster, buttons, _, _) in enumerate(movies[start:end], start):
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
            if poster:
                await message.answer_photo(poster, caption=text, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error sending movie {i}: {e}")
            await message.answer(f"Ошибка при отправке фильма {i}.")
            continue
    
    if len(movies) > end:
        await message.answer(
            "Показать ещё?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Следующие ➡️", callback_data=f"next_page_{page + 1}")]
            ])
        )

@dp.callback_query(lambda c: c.data.startswith('next_page_'))
async def handle_next_page(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split('_')[2])
    movies = (await state.get_data()).get("movies", [])
    if movies:
        await send_movies(callback_query.message, movies, page)

@dp.callback_query(lambda c: c.data.startswith('full_desc_'))
async def show_full_description(callback_query: types.CallbackQuery, state: FSMContext):
    index = int(callback_query.data.split('_')[2])
    movies = (await state.get_data()).get("movies", [])
    if 0 <= index < len(movies):
        await callback_query.message.answer(f"📜 Полное описание:\n{movies[index][3]}", parse_mode="Markdown")
    await callback_query.answer()

async def main():
    try:
        logger.info("Starting bot...")
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"Bot failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
