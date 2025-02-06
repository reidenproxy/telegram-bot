import os
import asyncpg
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# Логирование
logging.basicConfig(level=logging.INFO)

# Переменные окружения
TOKEN = os.getenv("7764737918:AAGnyZ0TnlI6ytCbV48S5vsHsoOgROZ1KwA")
DATABASE_URL = os.getenv("postgresql://${{PGUSER}}:${{POSTGRES_PASSWORD}}@${{RAILWAY_PRIVATE_DOMAIN}}:5432/${{PGDATABASE}}")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключение к базе данных
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            question TEXT,
            options TEXT,
            correct_answer TEXT
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            score INTEGER DEFAULT 0
        )
    """)
    await conn.close()

# Запуск базы данных
@dp.startup()
async def on_startup():
    await init_db()
    logging.info("База данных инициализирована!")

# Добавление вопроса
@dp.message(Command("add_question"))
async def add_question(message: Message):
    chat_id = message.chat.id
    parts = message.text.split('|')
    
    if len(parts) != 3:
        await message.answer("Ошибка! Формат: вопрос|варианты через запятую|правильный ответ")
        return
    
    question, options, correct_answer = map(str.strip, parts)
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("INSERT INTO quizzes (chat_id, question, options, correct_answer) VALUES ($1, $2, $3, $4)", 
                       chat_id, question, options, correct_answer)
    await conn.close()
    await message.answer("✅ Вопрос добавлен!")

# Начать викторину
@dp.message(Command("quiz"))
async def start_quiz(message: Message):
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT * FROM quizzes WHERE chat_id = $1 ORDER BY RANDOM() LIMIT 1", message.chat.id)
    await conn.close()
    
    if not row:
        await message.answer("❌ Вопросов пока нет!")
        return
    
    options = row["options"].split(',')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opt, callback_data=f"answer:{opt}|{row['correct_answer']}")]
        for opt in options
    ])
    await message.answer(row["question"], reply_markup=keyboard)

# Проверка ответа
@dp.callback_query(lambda c: c.data.startswith("answer:"))
async def check_answer(callback: types.CallbackQuery):
    user_answer, correct_answer = callback.data.split(":")[1].split("|")
    conn = await asyncpg.connect(DATABASE_URL)
    
    if user_answer == correct_answer:
        row = await conn.fetchrow("SELECT score FROM scores WHERE user_id = $1", callback.from_user.id)
        if row:
            new_score = row["score"] + 1
            await conn.execute("UPDATE scores SET score = $1 WHERE user_id = $2", new_score, callback.from_user.id)
        else:
            await conn.execute("INSERT INTO scores (user_id, username, score) VALUES ($1, $2, $3)", 
                               callback.from_user.id, callback.from_user.username, 1)
        await callback.message.answer("✅ Правильно! +1 балл")
    else:
        await callback.message.answer("❌ Неправильно!")
    
    await conn.close()
    await callback.answer()

# Проверка счёта
@dp.message(Command("score"))
async def check_score(message: Message):
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT score FROM scores WHERE user_id = $1", message.from_user.id)
    await conn.close()
    
    if row:
        await message.answer(f"🏆 Ваш счёт: {row['score']}")
    else:
        await message.answer("Вы ещё не участвовали в викторине!")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
