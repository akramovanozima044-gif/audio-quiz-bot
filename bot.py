import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv

# Environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

# Logging sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot va Dispatcher yaratish
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Quiz ma'lumotlari
QUIZ_DATA = [
    {
        "question": "Bu qaysi qo'shiq?",
        "audio_file": "audio1.mp3",  # Foydalanuvchi yuborishi kerak
        "options": ["Sevgi qo'shig'i", "Vatan qo'shig'i", "Dostlik qo'shig'i", "Tabiat qo'shig'i"],
        "correct_answer": 0
    },
    {
        "question": "Bu qaysi artistning qo'shig'i?",
        "audio_file": "audio2.mp3",
        "options": ["Shahzoda", "Jaloliddin Ahmadaliyev", "Ozoda", "Rayhon"],
        "correct_answer": 1
    }
]

# Foydalanuvchilarning holati
user_states = {}

# Start komandasi
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Quizni boshlash 🎵", callback_data="start_quiz"))
    keyboard.add(InlineKeyboardButton("Yordam ℹ️", callback_data="help"))
    
    await message.reply(
        "🎧 Audio Quiz Botga xush kelibsiz!\n\n"
        "Bu bot orqali musiqa bilimingizni sinab ko'rishingiz mumkin. "
        "Quiz davomida sizga audio fragmentlar beriladi va siz to'g'ri javobni topishingiz kerak.",
        reply_markup=keyboard
    )

# Yordam komandasi
@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await message.reply(
        "🤖 Botdan foydalanish:\n\n"
        "/start - Botni ishga tushirish\n"
        "/quiz - Yangi quiz boshlash\n"
        "/help - Yordam olish\n\n"
        "📌 Quiz qoidalari:\n"
        "1. Har bir savol uchun audio eshitasiz\n"
        "2. 4 ta variantdan to'g'ri javobni tanlang\n"
        "3. Quiz oxirida natijangizni ko'rasiz"
    )

# Quiz boshlash
@dp.callback_query_handler(lambda c: c.data == "start_quiz")
@dp.message_handler(commands=['quiz'])
async def start_quiz(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {
        'current_question': 0,
        'score': 0,
        'total_questions': len(QUIZ_DATA)
    }
    
    await send_question(user_id, message.chat.id)

async def send_question(user_id, chat_id):
    state = user_states[user_id]
    question_index = state['current_question']
    
    if question_index >= state['total_questions']:
        await finish_quiz(user_id, chat_id)
        return
    
    question = QUIZ_DATA[question_index]
    
    # Audio yuborish (hozircha faqat matn)
    await bot.send_message(
        chat_id,
        f"🎵 Savol {question_index + 1}/{state['total_questions']}\n\n"
        f"{question['question']}\n\n"
        f"Audio fragment yuborilmoqda..."
    )
    
    # Variantlar tugmalari
    keyboard = InlineKeyboardMarkup(row_width=2)
    for i, option in enumerate(question['options']):
        keyboard.insert(InlineKeyboardButton(option, callback_data=f"answer_{question_index}_{i}"))
    
    await bot.send_message(chat_id, "Variantlardan birini tanlang:", reply_markup=keyboard)

# Javobni tekshirish
@dp.callback_query_handler(lambda c: c.data.startswith('answer_'))
async def check_answer(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    _, question_index, answer_index = callback_query.data.split('_')
    question_index = int(question_index)
    answer_index = int(answer_index)
    
    if user_id not in user_states:
        await callback_query.answer("Quiz hozir boshlanmagan. /start ni bosing")
        return
    
    question = QUIZ_DATA[question_index]
    
    if answer_index == question['correct_answer']:
        user_states[user_id]['score'] += 1
        await callback_query.answer("✅ To'g'ri!", show_alert=True)
    else:
        correct_answer = question['options'][question['correct_answer']]
        await callback_query.answer(f"❌ Noto'g'ri! To'g'ri javob: {correct_answer}", show_alert=True)
    
    # Keyingi savolga o'tish
    user_states[user_id]['current_question'] += 1
    await send_question(user_id, callback_query.message.chat.id)

# Quizni tugatish
async def finish_quiz(user_id, chat_id):
    state = user_states[user_id]
    score = state['score']
    total = state['total_questions']
    
    percentage = (score / total) * 100
    
    if percentage >= 80:
        message = "🎉 Ajoyib natija! Siz musiqadan juda yaxshi tushunasiz!"
    elif percentage >= 60:
        message = "👍 Yaxshi natija! Yana bir bor urinib ko'ring."
    else:
        message = "💪 O'rganish uchun hamma vaqt joy bor. Qayta urinib ko'ring!"
    
    await bot.send_message(
        chat_id,
        f"📊 Quiz yakunlandi!\n\n"
        f"To'g'ri javoblar: {score}/{total}\n"
        f"Foiz: {percentage:.1f}%\n\n"
        f"{message}\n\n"
        f"Yana o'ynash uchun /quiz ni bosing"
    )
    
    # Foydalanuvchi holatini tozalash
    user_states.pop(user_id, None)

# Audio fayllarni qabul qilish (keyingi bosqichda rivojlantiriladi)
@dp.message_handler(content_types=['audio', 'voice'])
async def handle_audio(message: types.Message):
    await message.reply("🎵 Audio qabul qilindi! Bu funksiya keyingi yangilanishda qo'shiladi.")

# Xabar yuborish
@dp.message_handler()
async def echo_message(message: types.Message):
    await message.answer(
        "Men audio quiz botiman. Quizni boshlash uchun /quiz ni bosing yoki "
        "yordam olish uchun /help ni bosing."
    )

# Botni ishga tushirish
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)