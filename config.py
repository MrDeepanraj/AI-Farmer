import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")


def get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip().strip('"').strip("'")
