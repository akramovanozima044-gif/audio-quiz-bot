# handlers/common.py
from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Audio Quiz Bot - Yordam:\n"
        "/start - Botni ishga tushirish\n"
        "/help - Yordam\n"
        "/cancel - Amalni bekor qilish"
    )

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message):
    await message.answer("✅ Amal bekor qilindi. /start ni bosing.")