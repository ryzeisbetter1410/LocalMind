"""
LocalMind - Fully local student AI assistant via Telegram
Zero API costs. No rate limits. Your data stays on your machine.
"""

import asyncio
import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from core.router import MessageRouter
from schoology.client import SchoologyClient
from canvas.client import CanvasClient
from memory.store import MemoryStore
from config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    config = Config()
    config.validate()

    print("🧠 LocalMind starting up...")

    # Initialize memory
    memory = MemoryStore()

    # Auto-detect which LMS to use based on .env
    lms_client = None

    if config.CANVAS_TOKEN:
        print("📚 Syncing Canvas...")
        lms_client = CanvasClient(
            token=config.CANVAS_TOKEN,
            domain=config.CANVAS_DOMAIN
        )
        await lms_client.sync(memory)
        print(f"✅ Canvas synced: {len(memory.get_courses())} courses, {len(memory.get_assignments())} assignments")

    elif config.SCHOOLOGY_KEY and config.SCHOOLOGY_KEY != "skip":
        print("📚 Syncing Schoology...")
        lms_client = SchoologyClient(
            consumer_key=config.SCHOOLOGY_KEY,
            consumer_secret=config.SCHOOLOGY_SECRET,
            domain=config.SCHOOLOGY_DOMAIN
        )
        await lms_client.sync(memory)
        print(f"✅ Schoology synced: {len(memory.get_courses())} courses, {len(memory.get_assignments())} assignments")

    else:
        print("⚠️  No LMS configured — running without schedule data")
        print("   Add CANVAS_TOKEN or SCHOOLOGY_KEY to your .env to enable")

    # Initialize router
    router = MessageRouter(memory=memory, lms=lms_client, model=config.OLLAMA_MODEL)

    # Build Telegram app
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", router.handle_start))
    app.add_handler(CommandHandler("sync", router.handle_sync))
    app.add_handler(CommandHandler("help", router.handle_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router.handle_message))

    # Start reminder scheduler (only if job-queue is installed)
    job_queue = app.job_queue
    if job_queue:
        from datetime import time as dtime
        job_queue.run_daily(
            router.send_morning_digest,
            time=dtime(hour=8, minute=0),
            days=(0, 1, 2, 3, 4, 5, 6)
        )
        print("   Morning digest: enabled (8:00 AM daily)")
    else:
        print("   Morning digest: disabled (install python-telegram-bot[job-queue] to enable)")

    print("✅ LocalMind is live. Message your bot on Telegram!")
    print(f"   Model: {config.OLLAMA_MODEL}")
    print(f"   Topics: Schedule | Tutor | Study | General")

    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
