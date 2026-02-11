import os
from dotenv import load_dotenv

load_dotenv()

# Bot konfiguratsiyasi
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Database konfiguratsiyasi
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quiz.db")

# Fayllar uchun papka
UPLOADS_DIR = "uploads"
AUDIO_DIR = os.path.join(UPLOADS_DIR, "audio")

# Papkalarni yaratish
os.makedirs(AUDIO_DIR, exist_ok=True)