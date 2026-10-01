import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security & Session
SECRET_KEY = os.getenv("SECRET_KEY", "carevault-ai-super-secure-production-hackathon-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Storage
STORAGE_DIR = BASE_DIR / "storage" / "records"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_IMAGES_DIR = BASE_DIR / "app" / "static" / "sample_prescriptions"
SAMPLE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/carevault.db")
SQLITE_DB_PATH = BASE_DIR / "carevault.db"

# Max upload limit (15MB)
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".dcm"}

# Demo Mode Flag
DEMO_MODE = True
