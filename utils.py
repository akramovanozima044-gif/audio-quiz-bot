# utils.py - TO'LIQ TO'G'RILANGAN VERSIYA
import os
import uuid
from datetime import datetime
from aiogram.types import Message
import json
import aiofiles

# Audio fayllarni saqlash papkasi
AUDIO_DIR = "data/audio"

def ensure_audio_dir():
    """Audio papkasini yaratish (agar bo'lmasa)"""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    print(f"✅ Audio papkasi: {AUDIO_DIR}")

async def save_audio_file(audio_message: Message) -> str:
    """Audio faylni saqlash va yo'lini qaytarish (ASINCRON)"""
    ensure_audio_dir()
    
    try:
        # Fayl kengaytmasini to'g'ri olish
        if audio_message.audio.file_name:
            file_extension = audio_message.audio.file_name.split('.')[-1]
        else:
            file_extension = 'mp3'
        
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(AUDIO_DIR, unique_filename)
        
        print(f"📥 Audio yuklanmoqda: {unique_filename}")
        
        # 1-usul: destination bilan yuklash
        await audio_message.bot.download(
            file=audio_message.audio.file_id,
            destination=file_path
        )
        
        print(f"✅ Audio saqlandi: {file_path}")
        return file_path  # ✅ STRING qaytaramiz, coroutine emas!
        
    except Exception as e:
        print(f"❌ Audio saqlash xatosi: {e}")
        # 2-usul: get_file va download_file
        try:
            file_info = await audio_message.bot.get_file(audio_message.audio.file_id)
            downloaded_file = await audio_message.bot.download_file(file_info.file_path)
            
            # Faylni saqlash
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file.read())
            
            print(f"✅ Audio saqlandi (2-usul): {file_path}")
            return file_path
        except Exception as e2:
            print(f"❌ Ikkinchi usul ham xato: {e2}")
            return None

# Yoki oddiy sinxron versiya:
def save_audio_file_simple(audio_message: Message) -> str:
    """Oddiy sinxron versiya"""
    ensure_audio_dir()
    
    if audio_message.audio.file_name:
        file_extension = audio_message.audio.file_name.split('.')[-1]
    else:
        file_extension = 'mp3'
    
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(AUDIO_DIR, unique_filename)
    
    # Aiogram 3.x da bu ishlashi kerak
    audio_message.bot.download(
        audio_message.audio.file_id,
        destination=file_path
    )
    
    return file_path

def get_audio_file_url(file_path: str) -> str:
    """Audio faylning relative yo'lini qaytarish"""
    return file_path.replace("\\", "/")

def format_options(options_list: list) -> str:
    """Variantlarni JSON formatida saqlash uchun formatlash"""
    return json.dumps(options_list, ensure_ascii=False)

def parse_options(options_str: str) -> list:
    """JSON stringdan variantlarni olish"""
    try:
        return json.loads(options_str)
    except:
        # Agar xato bo'lsa, default variantlar
        return ["Variant 1", "Variant 2", "Variant 3", "Variant 4"]