import os
from dotenv import load_dotenv

load_dotenv()

# Bot konfiguratsiyasi
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN environment variable not set!")
    exit(1)

# ADMIN_ID ni olish
ADMIN_ID_str = os.getenv("ADMIN_ID", "0")
try:
    ADMIN_ID = int(ADMIN_ID_str)
except ValueError:
    print(f"⚠️ ADMIN_ID noto'g'ri format: {ADMIN_ID_str}, default 0 ishlatilmoqda")
    ADMIN_ID = 0

# Database konfiguratsiyasi
DATABASE_URL = os.getenv("DATABASE_URL")

# Agar Railway PostgreSQL yaratgan bo'lsa
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

print(f"✅ BOT_TOKEN mavjud: {bool(BOT_TOKEN)}")
print(f"✅ ADMIN_ID: {ADMIN_ID}")
print(f"✅ DATABASE_URL: {DATABASE_URL[:30]}..." if DATABASE_URL else "✅ DATABASE_URL: None")

# Fayllar uchun papka
import tempfile
UPLOADS_DIR = os.path.join(tempfile.gettempdir(), "uploads")
AUDIO_DIR = os.path.join(UPLOADS_DIR, "audio")

# Papkalarni yaratish
os.makedirs(AUDIO_DIR, exist_ok=True)
print(f"✅ UPLOADS_DIR: {UPLOADS_DIR}")