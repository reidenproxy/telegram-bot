import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, ChatMemberUpdatedFilter
from aiogram.types import Message, ChatMemberUpdated
from aiogram.exceptions import TelegramForbiddenError
import os

TOKEN = os.getenv("BOT_TOKEN")

from aiogram.client.default import DefaultBotProperties

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Фильтр для проверки админов чата
async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in {"administrator", "creator"}
    except TelegramForbiddenError:
        return False

# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer("Привет! Я бот для создания викторин.")

# Обработчик создания викторины (только для админов)
@dp.message(Command("create_quiz"))
async def create_quiz(message: Message):
    if not await is_admin(message.chat.id, message.from_user.id):
        await message.answer("❌ У вас нет прав на создание викторин!")
        return
    
    quiz_question = "Какого цвета небо?"
    options = ["Синее", "Зелёное", "Красное", "Жёлтое"]
    correct_option = 0  # Индекс правильного ответа
    
    await bot.send_poll(
        chat_id=message.from_user.id,  # Отправка викторины в личные сообщения
        question=quiz_question,
        options=options,
        type="quiz",
        correct_option_id=correct_option,
        explanation="Потому что атмосфера рассеивает солнечный свет!",
        is_anonymous=False
    )
    await message.answer("✅ Викторина создана и отправлена вам в ЛС!")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
