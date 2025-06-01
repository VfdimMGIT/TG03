
import sqlite3
import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=Config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('school_data.db')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        grade TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()


# Вызываем инициализацию БД при старте
init_db()


# Определение состояний
class Form(StatesGroup):
    name = State()
    age = State()
    grade = State()


# Команда /start - начало опроса
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("👋 Привет! Я помогу зарегистрировать студента. Как зовут студента?")
    await state.set_state(Form.name)


# Обработка имени
@dp.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Отлично! Сколько лет студенту?")
    await state.set_state(Form.age)


# Обработка возраста
@dp.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    # Проверяем, что возраст - число
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите число!")
        return

    await state.update_data(age=int(message.text))
    await message.answer("🏫 В каком классе учится студент? (например, 10А)")
    await state.set_state(Form.grade)


# Обработка класса и сохранение в БД
@dp.message(Form.grade)
async def process_grade(message: Message, state: FSMContext):
    await state.update_data(grade=message.text)
    user_data = await state.get_data()

    # Сохраняем данные в БД
    try:
        conn = sqlite3.connect('school_data.db')
        cur = conn.cursor()
        cur.execute('''
        INSERT INTO students (name, age, grade) 
        VALUES (?, ?, ?)
        ''', (user_data['name'], user_data['age'], user_data['grade']))
        conn.commit()
        conn.close()

        await message.answer(
            f"✅ Данные успешно сохранены!\n"
            f"👤 Имя: {user_data['name']}\n"
            f"🎂 Возраст: {user_data['age']}\n"
            f"🏫 Класс: {user_data['grade']}"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении в БД: {e}")
        await message.answer("❌ Произошла ошибка при сохранении данных. Попробуйте позже.")

    # Сбрасываем состояние
    await state.clear()


# Команда /view - просмотр всех студентов
@dp.message(Command("view"))
async def view_students(message: Message):
    try:
        conn = sqlite3.connect('school_data.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM students")
        students = cur.fetchall()
        conn.close()

        if not students:
            await message.answer("📭 В базе данных пока нет студентов.")
            return

        response = "📚 Список студентов:\n\n"
        for student in students:
            response += (
                f"ID: {student[0]}\n"
                f"👤 Имя: {student[1]}\n"
                f"🎂 Возраст: {student[2]}\n"
                f"🏫 Класс: {student[3]}\n"
                f"-----------------------\n"
            )

        await message.answer(response)
    except Exception as e:
        logger.error(f"Ошибка при чтении из БД: {e}")
        await message.answer("❌ Произошла ошибка при получении данных.")


# Команда /help
@dp.message(Command("help"))
async def help_cmd(message: Message):
    help_text = (
        "📚 Школьный бот - Помощь\n\n"
        "Доступные команды:\n"
        "/start - Начать регистрацию нового студента\n"
        "/view - Просмотреть всех зарегистрированных студентов\n"
        "/help - Показать это сообщение\n\n"
        "Чтобы добавить нового студента, просто нажмите /start и следуйте инструкциям."
    )
    await message.answer(help_text)


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
