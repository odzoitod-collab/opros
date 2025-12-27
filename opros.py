import asyncio
import logging
import sys
import json
import random
import aiosqlite

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- CONFIGURATION ---
BOT_TOKEN = "7236713833:AAGCM0zPW6lsHX_SF6kmOUGrakIZNAFu9mw"
ADMIN_ID = 844012884  # Твой Telegram ID

db_name = "new_year_party.db"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ШУТКИ ---
JOKES = [
    "Рожнов лох ",
    "Серьога порєшает",
    "А лизка захарченко сосала товсто..."
]

def random_joke() -> str:
    return random.choice(JOKES) if random.random() > 0.6 else ""

# --- DATABASE ---
async def init_db():
    async with aiosqlite.connect(db_name) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                telegram_username TEXT,
                display_name TEXT,
                guests_count INTEGER,
                drink_type TEXT,
                alcohol_details TEXT,
                soft_drinks TEXT,
                main_dish TEXT,
                main_dish_details TEXT,
                salad_1 TEXT,
                salad_2 TEXT,
                appetizers TEXT,
                sausage_types INTEGER,
                sausage_preferences TEXT,
                cheese_types INTEGER,
                cheese_preferences TEXT,
                bread_type TEXT,
                fruits TEXT,
                dessert TEXT,
                dessert_details TEXT,
                budget_per_person INTEGER,
                total_budget INTEGER,
                party_start_time TEXT,
                party_location TEXT,
                music_preferences TEXT,
                activities TEXT,
                dietary_restrictions TEXT,
                allergies TEXT,
                special_wishes TEXT,
                what_will_bring TEXT,
                completed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def save_survey(data: dict):
    async with aiosqlite.connect(db_name) as db:
        await db.execute("""
            INSERT INTO surveys (
                user_id, telegram_username, display_name, guests_count,
                drink_type, alcohol_details, soft_drinks,
                main_dish, main_dish_details, salad_1, salad_2,
                appetizers, sausage_types, sausage_preferences,
                cheese_types, cheese_preferences, bread_type, fruits,
                dessert, dessert_details, budget_per_person, total_budget,
                party_start_time, party_location, music_preferences, activities,
                dietary_restrictions, allergies, special_wishes, what_will_bring
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('user_id'), data.get('telegram_username'), data.get('display_name'), data.get('guests_count'),
            data.get('drink_type'), data.get('alcohol_details'), data.get('soft_drinks'),
            data.get('main_dish'), data.get('main_dish_details'), data.get('salad_1'), data.get('salad_2'),
            data.get('appetizers'), data.get('sausage_types'), data.get('sausage_preferences'),
            data.get('cheese_types'), data.get('cheese_preferences'), data.get('bread_type'), data.get('fruits'),
            data.get('dessert'), data.get('dessert_details'), data.get('budget_per_person'), data.get('total_budget'),
            data.get('party_start_time'), data.get('party_location'), data.get('music_preferences'), data.get('activities'),
            data.get('dietary_restrictions'), data.get('allergies'), data.get('special_wishes'), data.get('what_will_bring')
        ))
        await db.commit()

async def get_all_surveys():
    async with aiosqlite.connect(db_name) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM surveys ORDER BY completed_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_participants_count():
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM surveys")
        row = await cursor.fetchone()
        return row[0] if row else 0

# --- FSM STATES ---
class Survey(StatesGroup):
    name = State()
    guests_count = State()
    drink_type = State()
    alcohol_details = State()
    soft_drinks = State()
    main_dish = State()
    main_dish_details = State()
    salad_1 = State()
    salad_2 = State()
    appetizers = State()
    sausage_types = State()
    sausage_preferences = State()
    cheese_types = State()
    cheese_preferences = State()
    bread_type = State()
    fruits = State()
    dessert = State()
    dessert_details = State()
    budget = State()
    party_time = State()
    location = State()
    music = State()
    activities = State()
    dietary = State()
    allergies = State()
    special_wishes = State()
    what_bring = State()

# --- KEYBOARDS ---
def get_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📊 Статистика")]],
        resize_keyboard=True
    )

def get_drink_type_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍷 Алкоголь"), KeyboardButton(text="🧃 Безалкогольне")],
            [KeyboardButton(text="🍹 І те, і те")]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )

def get_yes_no_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Так"), KeyboardButton(text="❌ Ні")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def get_time_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="18:00"), KeyboardButton(text="19:00"), KeyboardButton(text="20:00")],
            [KeyboardButton(text="21:00"), KeyboardButton(text="22:00"), KeyboardButton(text="Ближче до півночі")]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )

def get_skip_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ Пропустити")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def get_location_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Вдома"), KeyboardButton(text="🏢 В гостях")],
            [KeyboardButton(text="🍽 Ресторан/кафе"), KeyboardButton(text="🤷 Ще не вирішили")]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )

# --- HANDLERS ---
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    joke = random_joke()
    text = f"🎄 Йоу! Плануємо Новий Рік!\n\n{joke}\n\nЯк тебе називати?" if joke else "🎄 Йоу! Плануємо Новий Рік!\n\nЯк тебе називати?"
    
    kb = get_admin_kb() if message.from_user.id == ADMIN_ID else ReplyKeyboardRemove()
    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await state.set_state(Survey.name)

@router.message(Survey.name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Ім'я закоротке, давай нормальне 😅")
        return
    
    await state.update_data(
        display_name=name,
        user_id=message.from_user.id,
        telegram_username=message.from_user.username or "немає"
    )
    
    joke = random_joke()
    text = f"Привіт, {name}! 🎉\n\n{joke}\n\n1️⃣ Скільки людей буде з тобою? (тільки число)" if joke else f"Привіт, {name}! 🎉\n\n1️⃣ Скільки людей буде з тобою? (тільки число)"
    await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await state.set_state(Survey.guests_count)

@router.message(Survey.guests_count)
async def process_guests(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Напиши число, не будь як Рожнов 🙄")
        return
    await state.update_data(guests_count=int(message.text))
    await message.answer("2️⃣ Які напої вживаєш?", reply_markup=get_drink_type_kb())
    await state.set_state(Survey.drink_type)

@router.message(Survey.drink_type)
async def process_drink_type(message: Message, state: FSMContext):
    drink_map = {"🍷 Алкоголь": "алкоголь", "🧃 Безалкогольне": "безалкогольне", "🍹 І те, і те": "все"}
    drink_type = drink_map.get(message.text, message.text.lower())
    await state.update_data(drink_type=drink_type)
    
    if drink_type in ["алкоголь", "все"]:
        await message.answer(
            "3️⃣ Який алкоголь любиш?\n(Шампанське, вино, горілка, коньяк, пиво...)",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Survey.alcohol_details)
    else:
        await state.update_data(alcohol_details="не п'є")
        await message.answer(
            "3️⃣ Які безалкогольні напої?\n(Сік, кола, вода, морс...)",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Survey.soft_drinks)

@router.message(Survey.alcohol_details)
async def process_alcohol(message: Message, state: FSMContext):
    await state.update_data(alcohol_details=message.text)
    await message.answer("4️⃣ А безалкогольне що? (сік, вода, кола...)")
    await state.set_state(Survey.soft_drinks)

@router.message(Survey.soft_drinks)
async def process_soft(message: Message, state: FSMContext):
    await state.update_data(soft_drinks=message.text)
    joke = random_joke()
    text = f"5️⃣ Яке гаряче хочеш на столі?\n(Курка, качка, м'ясо, риба...)\n\n{joke}" if joke else "5️⃣ Яке гаряче хочеш на столі?\n(Курка, качка, м'ясо, риба...)"
    await message.answer(text)
    await state.set_state(Survey.main_dish)

@router.message(Survey.main_dish)
async def process_main(message: Message, state: FSMContext):
    await state.update_data(main_dish=message.text)
    await message.answer("6️⃣ Як саме приготувати? (запечене, смажене, в духовці, на грилі...)")
    await state.set_state(Survey.main_dish_details)

@router.message(Survey.main_dish_details)
async def process_main_details(message: Message, state: FSMContext):
    await state.update_data(main_dish_details=message.text)
    await message.answer("7️⃣ Перший салат? (Олів'є, Шуба, Цезар, Крабовий...)")
    await state.set_state(Survey.salad_1)

@router.message(Survey.salad_1)
async def process_salad1(message: Message, state: FSMContext):
    await state.update_data(salad_1=message.text)
    await message.answer("8️⃣ Другий салат? (або напиши 'достатньо')")
    await state.set_state(Survey.salad_2)

@router.message(Survey.salad_2)
async def process_salad2(message: Message, state: FSMContext):
    await state.update_data(salad_2=message.text)
    joke = random_joke()
    text = f"9️⃣ Які закуски?\n(Канапки, тарталетки, бутерброди з ікрою, соління...)\n\n{joke}" if joke else "9️⃣ Які закуски?\n(Канапки, тарталетки, бутерброди з ікрою, соління...)"
    await message.answer(text)
    await state.set_state(Survey.appetizers)

@router.message(Survey.appetizers)
async def process_appetizers(message: Message, state: FSMContext):
    await state.update_data(appetizers=message.text)
    await message.answer("🔟 Скільки ВИДІВ ковбаси в нарізку? (число)")
    await state.set_state(Survey.sausage_types)

@router.message(Survey.sausage_types)
async def process_sausage_count(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Число давай! Серьога порєшає, а ти число напиши 😤")
        return
    await state.update_data(sausage_types=int(message.text))
    await message.answer("1️⃣1️⃣ Яку ковбасу любиш? (салямі, сервелат, балик...)")
    await state.set_state(Survey.sausage_preferences)

@router.message(Survey.sausage_preferences)
async def process_sausage_pref(message: Message, state: FSMContext):
    await state.update_data(sausage_preferences=message.text)
    await message.answer("1️⃣2️⃣ Скільки ВИДІВ сиру? (число)")
    await state.set_state(Survey.cheese_types)

@router.message(Survey.cheese_types)
async def process_cheese_count(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Рожнов теж не вмів рахувати... Число!")
        return
    await state.update_data(cheese_types=int(message.text))
    await message.answer("1️⃣3️⃣ Який сир? (Гауда, Маасдам, Бри, Дор Блю...)")
    await state.set_state(Survey.cheese_preferences)

@router.message(Survey.cheese_preferences)
async def process_cheese_pref(message: Message, state: FSMContext):
    await state.update_data(cheese_preferences=message.text)
    await message.answer("1️⃣4️⃣ Який хліб? (білий, чорний, багет, без хліба...)")
    await state.set_state(Survey.bread_type)

@router.message(Survey.bread_type)
async def process_bread(message: Message, state: FSMContext):
    await state.update_data(bread_type=message.text)
    await message.answer("1️⃣5️⃣ Які фрукти на стіл? (мандарини, виноград, яблука...)")
    await state.set_state(Survey.fruits)

@router.message(Survey.fruits)
async def process_fruits(message: Message, state: FSMContext):
    await state.update_data(fruits=message.text)
    joke = random_joke()
    text = f"1️⃣6️⃣ Який десерт?\n(Торт, тістечка, цукерки, морозиво...)\n\n{joke}" if joke else "1️⃣6️⃣ Який десерт?\n(Торт, тістечка, цукерки, морозиво...)"
    await message.answer(text)
    await state.set_state(Survey.dessert)

@router.message(Survey.dessert)
async def process_dessert(message: Message, state: FSMContext):
    await state.update_data(dessert=message.text)
    await message.answer("1️⃣7️⃣ Уточни десерт (який торт? які цукерки?)")
    await state.set_state(Survey.dessert_details)

@router.message(Survey.dessert_details)
async def process_dessert_details(message: Message, state: FSMContext):
    await state.update_data(dessert_details=message.text)
    await message.answer("1️⃣8️⃣ Твій бюджет НА ЛЮДИНУ в гривнях? (тільки число)")
    await state.set_state(Survey.budget)

@router.message(Survey.budget)
async def process_budget(message: Message, state: FSMContext):
    text = message.text.replace(" ", "").replace("грн", "").replace("₴", "")
    if not text.isdigit():
        await message.answer("Тільки число в гривнях! Без букв 💸")
        return
    
    data = await state.get_data()
    guests = data.get('guests_count', 1)
    budget = int(text)
    total = budget * (guests + 1)
    
    await state.update_data(budget_per_person=budget, total_budget=total)
    await message.answer(f"💰 Твій загальний бюджет: ~{total} грн\n\n1️⃣9️⃣ О котрій починаємо?", reply_markup=get_time_kb())
    await state.set_state(Survey.party_time)

@router.message(Survey.party_time)
async def process_time(message: Message, state: FSMContext):
    await state.update_data(party_start_time=message.text)
    await message.answer("2️⃣0️⃣ Де святкуємо?", reply_markup=get_location_kb())
    await state.set_state(Survey.location)

@router.message(Survey.location)
async def process_location(message: Message, state: FSMContext):
    await state.update_data(party_location=message.text)
    await message.answer("2️⃣1️⃣ Яка музика? (поп, реп, рок, ретро, мікс...)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Survey.music)

@router.message(Survey.music)
async def process_music(message: Message, state: FSMContext):
    await state.update_data(music_preferences=message.text)
    joke = random_joke()
    text = f"2️⃣2️⃣ Які активності?\n(Ігри, караоке, феєрверки, настолки...)\n\n{joke}" if joke else "2️⃣2️⃣ Які активності?\n(Ігри, караоке, феєрверки, настолки...)"
    await message.answer(text)
    await state.set_state(Survey.activities)

@router.message(Survey.activities)
async def process_activities(message: Message, state: FSMContext):
    await state.update_data(activities=message.text)
    await message.answer("2️⃣3️⃣ Є дієтичні обмеження?\n(Вегетаріанець, не їм свинину...)", reply_markup=get_skip_kb())
    await state.set_state(Survey.dietary)

@router.message(Survey.dietary)
async def process_dietary(message: Message, state: FSMContext):
    dietary = "" if message.text == "⏭ Пропустити" else message.text
    await state.update_data(dietary_restrictions=dietary)
    await message.answer("2️⃣4️⃣ Алергії на продукти?", reply_markup=get_skip_kb())
    await state.set_state(Survey.allergies)

@router.message(Survey.allergies)
async def process_allergies(message: Message, state: FSMContext):
    allergies = "" if message.text == "⏭ Пропустити" else message.text
    await state.update_data(allergies=allergies)
    await message.answer("2️⃣5️⃣ Особливі побажання до свята?", reply_markup=get_skip_kb())
    await state.set_state(Survey.special_wishes)

@router.message(Survey.special_wishes)
async def process_wishes(message: Message, state: FSMContext):
    wishes = "" if message.text == "⏭ Пропустити" else message.text
    await state.update_data(special_wishes=wishes)
    await message.answer("2️⃣6️⃣ Що ТИ принесеш на свято?\n(Їжу, напої, гроші, себе красивого...)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Survey.what_bring)

@router.message(Survey.what_bring)
async def process_bring(message: Message, state: FSMContext):
    await state.update_data(what_will_bring=message.text)
    
    data = await state.get_data()
    await save_survey(data)
    await state.clear()
    
    count = await get_participants_count()
    joke = random_joke()
    
    kb = get_admin_kb() if message.from_user.id == ADMIN_ID else ReplyKeyboardRemove()
    
    text = f"""✅ Готово, {data['display_name']}! Відповіді записані.

👥 Всього пройшли опитування: {count}

{joke}

Дякую! Чекай на результати 🎄"""
    
    await message.answer(text, reply_markup=kb)

# --- STATS ---
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    surveys = await get_all_surveys()
    if not surveys:
        await message.answer("📭 Поки ніхто не пройшов опитування", reply_markup=get_admin_kb())
        return
    
    # Формуємо звіт по кожному учаснику
    report = f"🎄 СТАТИСТИКА ОПИТУВАННЯ\n� Учасників: {len(surveys)}\n\n"
    
    total_budget = 0
    total_guests = 0
    
    for i, s in enumerate(surveys, 1):
        budget = s.get('budget_per_person') or 0
        guests = s.get('guests_count') or 0
        total_budget += s.get('total_budget') or 0
        total_guests += guests
        
        person_report = f"""━━━━━━━━━━━━━━━━━━
� {i }. {s.get('display_name', '?')} (@{s.get('telegram_username', '?')})
� Гостей: {guests}
💰 Бюджет: {budget} грн/люд ({s.get('total_budget', 0)} грн всього)

🍾 Напої: {s.get('drink_type', '-')}
   Алко: {s.get('alcohol_details', '-')}
   Безалко: {s.get('soft_drinks', '-')}

🍖 Гаряче: {s.get('main_dish', '-')} ({s.get('main_dish_details', '-')})

🥗 Салати: {s.get('salad_1', '-')}, {s.get('salad_2', '-')}

🍢 Закуски: {s.get('appetizers', '-')}

🧀 Нарізка:
   Ковбаса: {s.get('sausage_types', 0)} видів ({s.get('sausage_preferences', '-')})
   Сир: {s.get('cheese_types', 0)} видів ({s.get('cheese_preferences', '-')})

🍞 Хліб: {s.get('bread_type', '-')}
🍊 Фрукти: {s.get('fruits', '-')}
🍰 Десерт: {s.get('dessert', '-')} ({s.get('dessert_details', '-')})

⏰ Час: {s.get('party_start_time', '-')}
📍 Місце: {s.get('party_location', '-')}
🎵 Музика: {s.get('music_preferences', '-')}
🎮 Активності: {s.get('activities', '-')}

⚠️ Дієта: {s.get('dietary_restrictions', '-') or 'немає'}
🚫 Алергії: {s.get('allergies', '-') or 'немає'}
💭 Побажання: {s.get('special_wishes', '-') or 'немає'}
🎁 Принесе: {s.get('what_will_bring', '-')}

"""
        report += person_report
    
    report += f"""━━━━━━━━━━━━━━━━━━
📊 ЗАГАЛОМ:
👥 Людей (з гостями): {total_guests + len(surveys)}
💰 Загальний бюджет: {total_budget} грн

{random_joke()}
"""
    
    # Розбиваємо на частини якщо завелике
    if len(report) > 4000:
        parts = [report[i:i+4000] for i in range(0, len(report), 4000)]
        for part in parts:
            await message.answer(part, reply_markup=get_admin_kb())
    else:
        await message.answer(report, reply_markup=get_admin_kb())

@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    await state.clear()
    kb = get_admin_kb() if message.from_user.id == ADMIN_ID else ReplyKeyboardRemove()
    await message.answer("🔄 Скинуто. /start щоб почати знову", reply_markup=kb)

# --- MAIN ---
async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    await init_db()
    logger.info("✅ Bot started")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
