"""
Configuration — edit .env file, not this file
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")

    # Schoology
    SCHOOLOGY_KEY: str = os.getenv("SCHOOLOGY_KEY", "")
    SCHOOLOGY_SECRET: str = os.getenv("SCHOOLOGY_SECRET", "")
    SCHOOLOGY_DOMAIN: str = os.getenv("SCHOOLOGY_DOMAIN", "app.schoology.com")

    # Canvas
    CANVAS_TOKEN: str = os.getenv("CANVAS_TOKEN", "")
    CANVAS_DOMAIN: str = os.getenv("CANVAS_DOMAIN", "canvas.instructure.com")

    # Ollama
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3:mini")
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")

    # Topic IDs
    TOPIC_SCHEDULE: int = int(os.getenv("TOPIC_SCHEDULE", "0"))
    TOPIC_TUTOR: int = int(os.getenv("TOPIC_TUTOR", "0"))
    TOPIC_STUDY: int = int(os.getenv("TOPIC_STUDY", "0"))
    TOPIC_GENERAL: int = int(os.getenv("TOPIC_GENERAL", "0"))

    # Your Telegram chat ID
    ALLOWED_CHAT_ID: int = int(os.getenv("ALLOWED_CHAT_ID", "0"))

    def validate(self):
        missing = []
        if not self.TELEGRAM_TOKEN:
            missing.append("TELEGRAM_TOKEN")
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}\nCheck your .env file")
