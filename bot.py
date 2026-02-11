import os
import logging
import asyncio
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import F

# Token olish
TOKEN = os.environ.get('BOT_TOKEN')

if not TOKEN:
    # Local development uchun .env faylidan o'qish
    try:
        from dotenv import load_dotenv
        load_dotenv()
        TOKEN = os.getenv('BOT_TOKEN')
    except ImportError:
        pass

if not TOKEN:
    print("❌ XATO: BOT_TOKEN topilmadi!")
    print("Iltimos, Railway da BOT_TOKEN environment variable ni o'rnating")
    sys.exit(1)

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot va Dispatcher yaratish
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Quiz ma'lumotlari
QUIZ_DATA = [
    {
        "question": "Bu qaysi qo'shiq?",
        "audio_file": "audio1.mp3",
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

# /start komandasi
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Quizni boshlash 🎵", callback_data="start_quiz")],
            [InlineKeyboardButton(text="Yordam ℹ️", callback_data="help")]
        ]
    )
    
    await message.reply(
        "🎧 Audio Quiz Botga xush kelibsiz!\n\n"
        "Bu bot orqali musiqa bilimingizni sinab ko'rishingiz mumkin. "
        "Quiz davomida sizga audio fragmentlar beriladi va siz to'g'ri javobni topishingiz kerak.",
        reply_markup=keyboard
    )

# /help komandasi
@dp.message(Command("help"))
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

# /quiz komandasi
@dp.message(Command("quiz"))
async def start_quiz_command(message: types.Message):
    user_id = message.from_user.id
    user_states[user_id] = {
        'current_question': 0,
        'score': 0,
        'total_questions': len(QUIZ_DATA)
    }
    await send_question(user_id, message.chat.id)

# Start quiz callback
@dp.callback_query(F.data == "start_quiz")
async def start_quiz_callback(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    user_states[user_id] = {
        'current_question': 0,
        'score': 0,
        'total_questions': len(QUIZ_DATA)
    }
    await send_question(user_id, callback.message.chat.id)

async def send_question(user_id, chat_id):
    state = user_states.get(user_id)
    if not state:
        await bot.send_message(chat_id, "Iltimos, avval /start ni bosing")
        return
    
    question_index = state['current_question']
    
    if question_index >= state['total_questions']:
        await finish_quiz(user_id, chat_id)
        return
    
    question = QUIZ_DATA[question_index]
    
    # Savol matni
    await bot.send_message(
        chat_id,
        f"🎵 Savol {question_index + 1}/{state['total_questions']}\n\n"
        f"{question['question']}\n\n"
        f"🔊 Audio fragment yuborilmoqda... (demo rejim)"
    )
    
    # Variantlar tugmalari
    buttons = []
    for i, option in enumerate(question['options']):
        buttons.append([InlineKeyboardButton(
            text=option, 
            callback_data=f"answer_{question_index}_{i}"
        )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id, "Variantlardan birini tanlang:", reply_markup=keyboard)

# Javobni tekshirish
@dp.callback_query(F.data.startswith('answer_'))
async def check_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    data_parts = callback.data.split('_')
    
    if len(data_parts) != 3:
        await callback.answer("Xatolik yuz berdi")
        return
    
    _, question_index, answer_index = data_parts
    question_index = int(question_index)
    answer_index = int(answer_index)
    
    if user_id not in user_states:
        await callback.answer("Quiz hozir boshlanmagan. /start ni bosing", show_alert=True)
        return
    
    if question_index >= len(QUIZ_DATA):
        await callback.answer("Savol topilmadi", show_alert=True)
        return
    
    question = QUIZ_DATA[question_index]
    
    # Javobni tekshirish
    if answer_index == question['correct_answer']:
        user_states[user_id]['score'] += 1
        await callback.answer("✅ To'g'ri!", show_alert=True)
    else:
        correct_answer = question['options'][question['correct_answer']]
        await callback.answer(f"❌ Noto'g'ri! To'g'ri javob: {correct_answer}", show_alert=True)
    
    # Keyingi savolga o'tish
    user_states[user_id]['current_question'] += 1
    await send_question(user_id, callback.message.chat.id)

# Quizni tugatish
async def finish_quiz(user_id, chat_id):
    state = user_states.get(user_id)
    if not state:
        return
    
    score = state['score']
    total = state['total_questions']
    
    percentage = (score / total) * 100 if total > 0 else 0
    
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

# Help callback
@dp.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.answer()
    await send_help(callback.message)

# Audio fayllarni qabul qilish
@dp.message(F.audio | F.voice)
async def handle_audio(message: types.Message):
    await message.reply("🎵 Audio qabul qilindi! Bu funksiya keyingi yangilanishda qo'shiladi.")

# Boshqa xabarlarga javob
@dp.message()
async def echo_message(message: types.Message):
    await message.answer(
        "Men audio quiz botiman. Quizni boshlash uchun /quiz ni bosing yoki "
        "yordam olish uchun /help ni bosing.\n\n"
        "Boshlash uchun /start ni bosing."
    )

async def cleanup_webhook():
    """Webhook ni to'liq o'chirish"""
    logger.info("Webhook ni o'chirish jarayoni boshlandi...")
    
    try:
        # Webhook ni o'chirish
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook muvaffaqiyatli o'chirildi")
        return True
    except Exception as e:
        logger.error(f"❌ Webhook o'chirishda xatolik: {e}")
        return False

async def main():
    logger.info("=" * 50)
    logger.info("Audio Quiz Bot ishga tushmoqda...")
    logger.info("=" * 50)
    
    # 1. Webhook ni majburiy o'chirish
    logger.info("1. Webhook ni o'chirish...")
    success = await cleanup_webhook()
    
    if not success:
        logger.warning("Webhook o'chirishda muammo, qayta urinib ko'ramiz...")
        # Qayta urinib ko'rish
        await asyncio.sleep(2)
        success = await cleanup_webhook()
        
        if not success:
            logger.error("Webhook ni o'chirib bo'lmadi. Botni qayta ishga tushiring.")
            return
    
    # 2. Bot ma'lumotlarini olish
    logger.info("2. Bot ma'lumotlarini olish...")
    try:
        bot_info = await bot.get_me()
        logger.info(f"✅ Bot username: @{bot_info.username}")
        logger.info(f"✅ Bot ismi: {bot_info.first_name}")
        logger.info(f"✅ Bot ID: {bot_info.id}")
    except Exception as e:
        logger.error(f"❌ Bot ma'lumotlarini olishda xatolik: {e}")
        return
    
    # 3. Polling ni boshlash
    logger.info("3. Polling ni boshlash...")
    logger.info("✅ Bot muvaffaqiyatli ishga tushdi!")
    logger.info("=" * 50)
    
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"❌ Pollingda xatolik: {e}")
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi (Ctrl+C)")
    except Exception as e:
        logger.error(f"Kutilmagan xatolik: {e}")