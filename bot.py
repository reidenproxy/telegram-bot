import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Настройки
TOKEN = "7764737918:AAGnyZ0TnlI6ytCbV48S5vsHsoOgROZ1KwA"
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Функция для подключения к БД
async def init_db():
    async with aiosqlite.connect("quiz.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                chat_id INTEGER,
                question TEXT,
                options TEXT,
                correct_answer TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                score INTEGER DEFAULT 0
            )
        """)
        await db.commit()

# Хэндлер для создания викторины
@dp.message(Command("создать_викторину"))
async def create_quiz(message: Message):
    await message.answer("Отправьте вопрос и варианты ответа в формате:\n\n"
                         "<b>вопрос | ответ1, ответ2, ответ3 | правильный ответ</b>")

# Хэндлер для добавления вопроса
@dp.message(F.text.func(lambda text: "|" in text))
async def add_question(message: Message):
    chat_id = message.chat.id
    parts = message.text.split('|')
    
    if len(parts) != 3:
        await message.answer("Ошибка! Убедитесь, что формат правильный.")
        return

    question, options, correct_answer = map(str.strip, parts)

    async with aiosqlite.connect("quiz.db") as db:
        await db.execute("INSERT INTO quizzes VALUES (?, ?, ?, ?)", (chat_id, question, options, correct_answer))
        await db.commit()

    await message.answer("✅ Вопрос добавлен!")

# Хэндлер для запуска викторины
@dp.message(Command("старт_викторину"))
async def start_quiz(message: Message):
    chat_id = message.chat.id

    async with aiosqlite.connect("quiz.db") as db:
        cursor = await db.execute("SELECT question, options, correct_answer FROM quizzes WHERE chat_id=?", (chat_id,))
        questions = await cursor.fetchall()

    if not questions:
        await message.answer("❌ Викторина не найдена. Добавьте вопросы!")
        return
    
    for question, options, correct_answer in questions:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=opt.strip(), callback_data=f"answer:{opt.strip()}|{correct_answer}")]
                for opt in options.split(',')
            ]
        )
        await message.answer(question, reply_markup=markup)

# Хэндлер для проверки ответа
@dp.callback_query(F.data.startswith("answer:"))
async def check_answer(callback: types.CallbackQuery):
    user_answer, correct_answer = callback.data.split(":")[1].split("|")

    if user_answer == correct_answer:
        async with aiosqlite.connect("quiz.db") as db:
            cursor = await db.execute("SELECT score FROM scores WHERE user_id=?", (callback.from_user.id,))
            row = await cursor.fetchone()

            if row:
                new_score = row[0] + 1
                await db.execute("UPDATE scores SET score=? WHERE user_id=?", (new_score, callback.from_user.id))
            else:
                await db.execute("INSERT INTO scores (user_id, username, score) VALUES (?, ?, ?)",
                                 (callback.from_user.id, callback.from_user.username, 1))

            await db.commit()

        await callback.message.answer("✅ Правильно! +1 балл")
    else:
        await callback.message.answer("❌ Неправильно!")

    await callback.answer()

# Хэндлер для вывода рейтинга
@dp.message(Command("рейтинг"))
async def show_scores(message: Message):
    async with aiosqlite.connect("quiz.db") as db:
        cursor = await db.execute("SELECT username, score FROM scores ORDER BY score DESC LIMIT 10")
        rows = await cursor.fetchall()

    if not rows:
        await message.answer("Пока никто не набрал очков.")
        return

    leaderboard = "🏆 <b>Топ игроков:</b>\n\n"
    for i, (username, score) in enumerate(rows, start=1):
        leaderboard += f"{i}. {username}: {score} баллов\n"

    await message.answer(leaderboard)

# Основная функция запуска
async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())