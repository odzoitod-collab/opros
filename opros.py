import asyncio
import logging
import sys
import os
import random
import aiosqlite
from datetime import datetime

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN") or "7236713833:AAGCM0zPW6lsHX_SF6kmOUGrakIZNAFu9mw"
ADMIN_ID = int(os.getenv("ADMIN_ID") or "844012884")

db_name = "new_year_party.db"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- ШУТКИ ---
JOKES = [
    "Рожнов лох 😂",
    "Серьога порєшає! 💪",
    "Хто не скине — той Рожнов 🤡",
    "Новий рік буде вогонь, якщо Серьога не проспить 😴",
    "Олів'є без ковбаси — як Рожнов без зашквару 🥗",
    "Серьога каже: 'Я принесу!' — ніхто не вірить 😏",
    "Рожнов обіцяв шампанське... чекаємо з 2019 🍾",
    "Головне — не бути як Рожнов на минулий НР 🙈",
    "Серьога — легенда, Рожнов — мем 🏆",
    "Якщо щось піде не так — виною Рожнов 🎯",
    "Рожнов вже гуглить 'як не облажатись на НР' 🔍",
    "Серьога: 'Я організую!' Всі: 'О ні...' 😅"
]

def random_joke() -> str:
    return random.choice(JOKES) if random.random() > 0.5 else ""

def joke_text(base: str) -> str:
    joke = random_joke()
    return f"{base}\n\n{joke}" if joke else base

# --- DATABASE ---
async def init_db():
    async with aiosqlite.connect(db_name) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                telegram_username TEXT,
                display_name TEXT,
                people_count TEXT,
                drinks TEXT,
                food TEXT,
                snacks_and_cuts TEXT,
                dessert TEXT,
                budget TEXT,
                time_and_place TEXT,
                activities TEXT,
                restrictions TEXT,
                contribution TEXT,
                extra_wishes TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await db.commit()
    logger.info("Database initialized")

async def save_survey(data: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.execute("SELECT id FROM surveys WHERE user_id = ?", (data['user_id'],))
        exists = await cursor.fetchone()
        
        if exists:
            await db.execute("""
                UPDATE surveys SET
                    telegram_username = ?, display_name = ?, people_count = ?,
                    drinks = ?, food = ?, snacks_and_cuts = ?, dessert = ?,
                    budget = ?, time_and_place = ?, activities = ?,
                    restrictions = ?, contribution = ?, extra_wishes = ?, updated_at = ?
                WHERE user_id = ?
            """, (
                data.get('telegram_username'), data.get('display_name'), data.get('people_count'),
                data.get('drinks'), data.get('food'), data.get('snacks_and_cuts'), data.get('dessert'),
                data.get('budget'), data.get('time_and_place'), data.get('activities'),
                data.get('restrictions'), data.get('contribution'), data.get('extra_wishes'), now,
                data['user_id']
            ))
        else:
            await db.execute("""
                INSERT INTO surveys (
                    user_id, telegram_username, display_name, people_count,
                    drinks, food, snacks_and_cuts, dessert, budget,
                    time_and_place, activities, restrictions, contribution, extra_wishes,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['user_id'], data.get('telegram_username'), data.get('display_name'), data.get('people_count'),
                data.get('drinks'), data.get('food'), data.get('snacks_and_cuts'), data.get('dessert'),
                data.get('budget'), data.get('time_and_place'), data.get('activities'),
                data.get('restrictions'), data.get('contribution'), data.get('extra_wishes'),
                now, now
            ))
        await db.commit()
    logger.info(f"Survey saved for user {data['user_id']}")

async def get_all_surveys():
    async with aiosqlite.connect(db_name) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM surveys ORDER BY updated_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def get_survey_count():
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM surveys")
        row = await cursor.fetchone()
        return row[0] if row else 0

async def delete_survey(user_id: int):
    async with aiosqlite.connect(db_name) as db:
        await db.execute("DELETE FROM surveys WHERE user_id = ?", (user_id,))
        await db.commit()

# --- FSM STATES ---
class Survey(StatesGroup):
    name = State()
    people = State()
    drinks = State()
    food = State()
    snacks = State()
    dessert = State()
    budget = State()
    time_place = State()
    activities = State()
    restrictions = State()
    contribution = State()
    extra = State()

# --- KEYBOARDS ---
def admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📊 Статистика")]],
        resize_keyboard=True
    )

def skip_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏭ Пропустити")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def remove_kb():
    return ReplyKeyboardRemove()

# --- HANDLERS ---
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    logger.info(f"User {message.from_user.id} started bot")
    text = joke_text("🎄 Йоу! Плануємо Новий Рік разом!\n\nОпитування займе 2-3 хвилини.\nВідповідай розгорнуто — так буде легше все спланувати.\n\n👤 Як тебе називати?")
    await message.answer(text, reply_markup=remove_kb())
    await state.set_state(Survey.name)

@router.message(Survey.name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Занадто коротко, напиши нормальне ім'я 😅")
        return
    
    await state.update_data(
        display_name=name,
        user_id=message.from_user.id,
        telegram_username=message.from_user.username or "без юзернейму"
    )
    
    text = joke_text(f"Привіт, {name}! 🎉\n\n1️⃣ Скільки вас буде? Ти + скільки гостей?\n\n(Наприклад: 'Я сам', 'Я + дівчина', 'Нас буде 4')")
    await message.answer(text)
    await state.set_state(Survey.people)

@router.message(Survey.people)
async def process_people(message: Message, state: FSMContext):
    await state.update_data(people_count=message.text)
    
    text = joke_text("""2️⃣ НАПОЇ 🍾

Розкажи все про напої:
• Алкоголь чи без? Що саме?
• Шампанське, вино, горілка, коньяк, пиво?
• Соки, кола, вода, морс?
• Скільки приблизно потрібно?

(Пиши все в одному повідомленні)""")
    await message.answer(text)
    await state.set_state(Survey.drinks)

@router.message(Survey.drinks)
async def process_drinks(message: Message, state: FSMContext):
    await state.update_data(drinks=message.text)
    
    text = joke_text("""3️⃣ ОСНОВНА ЇЖА 🍖

Розкажи про гаряче та салати:
• Яке гаряче? (курка, качка, м'ясо, риба)
• Як готувати? (запечене, смажене, на грилі)
• Які салати? (Олів'є, Шуба, Цезар, інші)
• Скільки видів салатів потрібно?

(Все в одному повідомленні)""")
    await message.answer(text)
    await state.set_state(Survey.food)

@router.message(Survey.food)
async def process_food(message: Message, state: FSMContext):
    await state.update_data(food=message.text)
    
    text = joke_text("""4️⃣ ЗАКУСКИ ТА НАРІЗКИ 🧀

Розкажи про:
• Ковбасна нарізка — скільки видів? Які? (салямі, балик, сервелат)
• Сирна нарізка — скільки видів? Які? (Гауда, Маасдам, Бри)
• Інші закуски? (канапки, тарталетки, соління, оливки, ікра)
• Хліб? (білий, чорний, багет)
• Фрукти? (мандарини, виноград, яблука)""")
    await message.answer(text)
    await state.set_state(Survey.snacks)

@router.message(Survey.snacks)
async def process_snacks(message: Message, state: FSMContext):
    await state.update_data(snacks_and_cuts=message.text)
    
    text = joke_text("""5️⃣ ДЕСЕРТ 🍰

Що на солодке?
• Торт? Який саме?
• Тістечка, цукерки?
• Морозиво?
• Щось інше?""")
    await message.answer(text)
    await state.set_state(Survey.dessert)

@router.message(Survey.dessert)
async def process_dessert(message: Message, state: FSMContext):
    await state.update_data(dessert=message.text)
    
    text = """6️⃣ БЮДЖЕТ 💰

Скільки готовий скинути на спільний стіл?
(Напиши суму в гривнях, наприклад: 500, 1000, 1500)"""
    await message.answer(text)
    await state.set_state(Survey.budget)

@router.message(Survey.budget)
async def process_budget(message: Message, state: FSMContext):
    await state.update_data(budget=message.text)
    
    text = joke_text("""7️⃣ ЧАС І МІСЦЕ 📍

• О котрій хочеш почати святкувати?
• Де збираємось? (вдома у когось, ресторан, інше)
• Є побажання по локації?""")
    await message.answer(text)
    await state.set_state(Survey.time_place)

@router.message(Survey.time_place)
async def process_time_place(message: Message, state: FSMContext):
    await state.update_data(time_and_place=message.text)
    
    text = joke_text("""8️⃣ РОЗВАГИ 🎮

Чим хочеш займатись на святі?
• Музика? Яка? (поп, реп, ретро, мікс)
• Ігри? Настолки? Караоке?
• Феєрверки, бенгальські вогні?
• Щось особливе?""")
    await message.answer(text)
    await state.set_state(Survey.activities)

@router.message(Survey.activities)
async def process_activities(message: Message, state: FSMContext):
    await state.update_data(activities=message.text)
    
    text = """9️⃣ ОБМЕЖЕННЯ ⚠️

Є щось важливе?
• Алергії на продукти?
• Дієта? (вегетаріанець, не їси свинину, інше)
• Щось не їси принципово?

(Якщо нема — напиши 'нема' або натисни пропустити)"""
    await message.answer(text, reply_markup=skip_kb())
    await state.set_state(Survey.restrictions)

@router.message(Survey.restrictions)
async def process_restrictions(message: Message, state: FSMContext):
    text = "" if message.text == "⏭ Пропустити" else message.text
    await state.update_data(restrictions=text)
    
    text = joke_text("""🔟 ТВІЙ ВНЕСОК 🎁

Що ТИ можеш принести або зробити?
• Приготувати щось? Що саме?
• Принести напої?
• Скинути грошима?
• Допомогти з організацією?
• Принести настолки/колонку/щось інше?""")
    await message.answer(text, reply_markup=remove_kb())
    await state.set_state(Survey.contribution)

@router.message(Survey.contribution)
async def process_contribution(message: Message, state: FSMContext):
    await state.update_data(contribution=message.text)
    
    text = """1️⃣1️⃣ ДОДАТКОВО 💭

Є ще щось важливе, що я не спитав?
Будь-які побажання, ідеї, пропозиції?

(Або натисни пропустити)"""
    await message.answer(text, reply_markup=skip_kb())
    await state.set_state(Survey.extra)

@router.message(Survey.extra)
async def process_extra(message: Message, state: FSMContext):
    text = "" if message.text == "⏭ Пропустити" else message.text
    await state.update_data(extra_wishes=text)
    
    data = await state.get_data()
    await save_survey(data)
    await state.clear()
    
    count = await get_survey_count()
    kb = admin_kb() if message.from_user.id == ADMIN_ID else remove_kb()
    
    finish_text = joke_text(f"""✅ Дякую, {data['display_name']}! Все записано!

👥 Пройшли опитування: {count} чол.

Якщо захочеш змінити відповіді — просто напиши /start знову.

🎄 До зустрічі на святі!""")
    
    await message.answer(finish_text, reply_markup=kb)

# --- STATS ---
@router.message(F.text == "📊 Статистика")
async def cmd_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    logger.info(f"Admin {message.from_user.id} requested stats")
    
    surveys = await get_all_surveys()
    if not surveys:
        await message.answer("📭 Поки ніхто не пройшов опитування", reply_markup=admin_kb())
        return
    
    header = f"🎄 НОВОРІЧНЕ ОПИТУВАННЯ\n📊 Відповідей: {len(surveys)}\n"
    header += "━" * 30 + "\n\n"
    
    reports = [header]
    
    for i, s in enumerate(surveys, 1):
        person = f"""👤 {i}. {s.get('display_name', '?')} (@{s.get('telegram_username', '?')})
📅 Оновлено: {s.get('updated_at', '?')}

👥 Людей: {s.get('people_count', '-')}

🍾 НАПОЇ:
{s.get('drinks', '-')}

🍖 ЇЖА (гаряче + салати):
{s.get('food', '-')}

🧀 ЗАКУСКИ І НАРІЗКИ:
{s.get('snacks_and_cuts', '-')}

🍰 ДЕСЕРТ:
{s.get('dessert', '-')}

💰 БЮДЖЕТ: {s.get('budget', '-')} грн

📍 ЧАС І МІСЦЕ:
{s.get('time_and_place', '-')}

🎮 РОЗВАГИ:
{s.get('activities', '-')}

⚠️ ОБМЕЖЕННЯ:
{s.get('restrictions', '-') or 'немає'}

🎁 ПРИНЕСЕ/ЗРОБИТЬ:
{s.get('contribution', '-')}

💭 ДОДАТКОВО:
{s.get('extra_wishes', '-') or 'немає'}

{"━" * 30}

"""
        reports.append(person)
    
    joke = random_joke()
    if joke:
        reports.append(f"\n{joke}")
    
    current_msg = ""
    for report in reports:
        if len(current_msg) + len(report) > 4000:
            await message.answer(current_msg, reply_markup=admin_kb())
            current_msg = report
        else:
            current_msg += report
    
    if current_msg:
        await message.answer(current_msg, reply_markup=admin_kb())

@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    await state.clear()
    kb = admin_kb() if message.from_user.id == ADMIN_ID else remove_kb()
    await message.answer("🔄 Скинуто. /start щоб почати знову", reply_markup=kb)

@router.message(Command("delete_my_data"))
async def cmd_delete(message: Message, state: FSMContext):
    await state.clear()
    await delete_survey(message.from_user.id)
    kb = admin_kb() if message.from_user.id == ADMIN_ID else remove_kb()
    await message.answer("🗑 Твої дані видалено з бази", reply_markup=kb)

# --- MAIN ---
async def main():
    logger.info(f"Starting bot with token: {BOT_TOKEN[:10]}...")
    logger.info(f"Admin ID: {ADMIN_ID}")
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    await init_db()
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot started polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
