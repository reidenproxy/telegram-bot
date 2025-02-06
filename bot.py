import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.utils import executor
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан. Проверь .env файл.")

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Получение списка администраторов чата
async def get_chat_admins(chat_id):
    chat_administrators = await bot.get_chat_administrators(chat_id)
    return [admin.user.id for admin in chat_administrators]

# Проверка, является ли пользователь администратором
async def is_admin(message: Message):
    admins = await get_chat_admins(message.chat.id)
    return message.from_user.id in admins

# Обработчик команды /start
@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer("Привет! Я бот для создания вопросов в чате. Только администраторы могут их добавлять.")

# Обработчик команды /ask (только для админов)
@dp.message(Command("ask"))
async def ask_command(message: Message):
    if not await is_admin(message):
        await message.answer("Вы не администратор этого чата и не можете создавать вопросы.")
        return
    
    question = message.text[len("/ask "):]  # Получаем текст вопроса
    if not question:
        await message.answer("Пожалуйста, укажите вопрос после команды /ask.")
        return
    
    await message.answer(f"Вопрос добавлен: {question}")

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
