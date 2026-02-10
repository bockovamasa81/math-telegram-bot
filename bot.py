
import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# =======================
# 🔑 TOKEN
# =======================
import os
TOKEN = os.getenv("BOT_TOKEN")


bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# =======================
# 📸 ЗАДАНИЯ (file_id)
# =======================
TASKS = [
  {
    "id": 1,
    "file_id": "AgACAgIAAxkBAANNaYrxApPvLClbGKM9tA_5_Oy0IDMAAokTaxvDXVhIz9j2c9Jyr5EBAAMCAAN4AAM6BA",
    "answer": "24",
    "alt": [],
    "explain": ""
  },
  {
    "id": 2,
    "file_id": "AgACAgIAAxkBAANPaYrxWajtTm35X2DM09zZV2_K9dcAAosTaxvDXVhIDYhNMQzx0cABAAMCAAN4AAM6BA",
    "answer": "36",
    "alt": [],
    "explain": ""
  },
  {
    "id": 3,
    "file_id": "AgACAgIAAxkBAANRaYrxa5O_vgGNGWTDx1u2QKhbztsAAowTaxvDXVhIUMM04j4-LKUBAAMCAAN4AAM6BA",
    "answer": "46",
    "alt": [],
    "explain": ""
  },
  {
    "id": 4,
    "file_id": "AgACAgIAAxkBAANTaYrxmnJQGNBqJa89EhY2YIQw5tQAApATaxvDXVhIw3d35p0zMIEBAAMCAAN4AAM6BA",
    "answer": "0.08",
    "alt": ["0,08"],
    "explain": ""
  },
  {
    "id": 5,
    "file_id": "AgACAgIAAxkBAANVaYrxu0Qu3yrycTfj_n_ijxV7X-UAApETaxvDXVhIsJRY1sB6FcQBAAMCAAN4AAM6BA",
    "answer": "0.91",
    "alt": ["0,91"],
    "explain": ""
  },
]

# =======================
# 🧠 ХРАНИЛИЩА
# =======================
USERS = {}
SESSIONS = {}

# =======================
# FSM
# =======================
class Reg(StatesGroup):
    name = State()
    grade = State()
    time = State()
    minutes = State()

class Practice(StatesGroup):
    answering = State()

# =======================
# 🧩 КЛАВИАТУРЫ
# =======================
def grade_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="10 класс", callback_data="grade:10")
    kb.button(text="11 класс", callback_data="grade:11")
    kb.adjust(2)
    return kb.as_markup()

def time_kb():
    kb = InlineKeyboardBuilder()
    for t in ["15:00", "17:00", "19:00", "21:00"]:
        kb.button(text=t, callback_data=f"time:{t}")
    kb.adjust(2)
    return kb.as_markup()

def minutes_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="15 минут (5 задач)", callback_data="min:15")
    kb.button(text="30 минут (10 задач)", callback_data="min:30")
    kb.adjust(1)
    return kb.as_markup()

def menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🚀 Начать практику", callback_data="menu:practice")
    kb.adjust(1)
    return kb.as_markup()

def next_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="➡️ Следующая", callback_data="next")
    return kb.as_markup()

def finish_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 К итогам", callback_data="finish")
    return kb.as_markup()

def wrong_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔁 Попробовать ещё", callback_data="retry")
    kb.button(text="👀 Показать ответ", callback_data="show")
    kb.adjust(2)
    return kb.as_markup()

# =======================
# 🔧 ВСПОМОГАТЕЛЬНЫЕ
# =======================
def normalize(s: str) -> str:
    return s.strip().replace(",", ".").lower()

def check_answer(user_input, task):
    ui = normalize(user_input)
    if ui == normalize(task["answer"]):
        return True
    return ui in {normalize(x) for x in task.get("alt", [])}

def pct(a, b):
    return round(100 * a / b, 1) if b else 0

def daily_count(user_id):
    return 5 if USERS[user_id]["minutes"] == 15 else 10

# =======================
# 🚀 /start
# =======================
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    uid = message.from_user.id
    if uid in USERS:
        await message.answer("С возвращением! Готовы к практике?", reply_markup=menu_kb())
        return
    await message.answer("Как тебя зовут?")
    await state.set_state(Reg.name)

@dp.message(Reg.name)
async def reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("В каком ты классе?", reply_markup=grade_kb())
    await state.set_state(Reg.grade)

@dp.callback_query(Reg.grade)
async def reg_grade(callback: CallbackQuery, state: FSMContext):
    await state.update_data(grade=callback.data.split(":")[1])
    await callback.message.edit_text("Во сколько присылать напоминание?", reply_markup=time_kb())
    await state.set_state(Reg.time)
    await callback.answer()

@dp.callback_query(Reg.time)
async def reg_time(callback: CallbackQuery, state: FSMContext):
    await state.update_data(time=callback.data.split(":")[1])
    await callback.message.edit_text("Сколько времени готов(а) заниматься?", reply_markup=minutes_kb())
    await state.set_state(Reg.minutes)
    await callback.answer()

@dp.callback_query(Reg.minutes)
async def reg_minutes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    uid = callback.from_user.id
    USERS[uid] = {
        **data,
        "minutes": int(callback.data.split(":")[1]),
        "total": 0,
        "correct": 0,
        "first": 0
    }
    await state.clear()
    await callback.message.edit_text("Регистрация завершена 🚀", reply_markup=menu_kb())
    await callback.answer()

# =======================
# 🧠 ПРАКТИКА
# =======================
@dp.callback_query(F.data == "menu:practice")
async def start_practice(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    count = min(daily_count(uid), len(TASKS))
    tasks = random.sample(TASKS, count)

    SESSIONS[uid] = {
        "tasks": tasks,
        "i": 0,
        "correct": 0,
        "first": 0,
        "wrong": 0,
        "prev_acc": pct(USERS[uid]["correct"], USERS[uid]["total"])
    }

    await state.set_state(Practice.answering)
    task = tasks[0]
    await bot.send_photo(callback.message.chat.id, task["file_id"], caption="Задача 1\nВведи ответ")
    await callback.answer()

@dp.message(Practice.answering)
async def answer(message: Message):
    uid = message.from_user.id
    s = SESSIONS[uid]
    task = s["tasks"][s["i"]]

    if check_answer(message.text, task):
        s["correct"] += 1
        if s["wrong"] == 0:
            s["first"] += 1
        s["wrong"] = 0

        kb = finish_kb() if s["i"] == len(s["tasks"]) - 1 else next_kb()
        await message.answer("✅ Верно!", reply_markup=kb)
    else:
        s["wrong"] += 1
        if s["wrong"] >= 2:
            await message.answer("❌ Неверно", reply_markup=wrong_kb())
        else:
            await message.answer("❌ Неверно, попробуй ещё")

@dp.callback_query(F.data == "next")
async def next_task(callback: CallbackQuery):
    uid = callback.from_user.id
    s = SESSIONS[uid]
    s["i"] += 1
    s["wrong"] = 0
    task = s["tasks"][s["i"]]
    await bot.send_photo(callback.message.chat.id, task["file_id"], caption=f"Задача {s['i']+1}\nВведи ответ")
    await callback.answer()

@dp.callback_query(F.data == "retry")
async def retry(callback: CallbackQuery):
    await callback.message.answer("Попробуй ещё раз")

@dp.callback_query(F.data == "show")
async def show(callback: CallbackQuery):
    uid = callback.from_user.id
    s = SESSIONS[uid]
    task = s["tasks"][s["i"]]
    await callback.message.answer(f"Ответ: {task['answer']}", reply_markup=finish_kb() if s["i"] == len(s["tasks"]) - 1 else next_kb())
    s["wrong"] = 0
    await callback.answer()

@dp.callback_query(F.data == "finish")
async def finish(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    s = SESSIONS.pop(uid)
    u = USERS[uid]

    u["total"] += len(s["tasks"])
    u["correct"] += s["correct"]
    u["first"] += s["first"]

    acc = pct(u["correct"], u["total"])
    delta = round(acc - s["prev_acc"], 1)

    await state.clear()
    await callback.message.answer(
        f"📊 Итоги\n\n"
        f"Сегодня: {s['correct']} / {len(s['tasks'])}\n"
        f"С первого раза: {s['first']}\n\n"
        f"За всё время: {acc}% ({'+' if delta>0 else ''}{delta} п.п.)"
    )
    await callback.answer()

# =======================
async def main():
    await dp.start_polling(bot)

await main()
