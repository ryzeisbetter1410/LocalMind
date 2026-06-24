"""
Message router — reads which Telegram topic the message came from
and routes to the right AI mode with the right system prompt.
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from core.ollama import OllamaClient
from core.prompts import schedule_prompt, tutor_prompt, study_prompt, general_prompt
from memory.store import MemoryStore

from config import Config

logger = logging.getLogger(__name__)
config = Config()

# Per-chat conversation history (in-memory, resets on restart)
# Format: {chat_id: {thread_id: [{"role": ..., "content": ...}]}}
_histories: dict = {}


def _get_history(chat_id: int, thread_id: int) -> list:
    return _histories.setdefault(chat_id, {}).setdefault(thread_id, [])


def _add_to_history(chat_id: int, thread_id: int, role: str, content: str):
    history = _get_history(chat_id, thread_id)
    history.append({"role": role, "content": content})
    # Keep last 20 messages to avoid context overflow
    if len(history) > 20:
        history.pop(0)


def _detect_topic_mode(thread_id: int) -> str:
    """Map thread ID to mode name."""
    mapping = {
        config.TOPIC_SCHEDULE: "schedule",
        config.TOPIC_TUTOR: "tutor",
        config.TOPIC_STUDY: "study",
        config.TOPIC_GENERAL: "general",
    }
    return mapping.get(thread_id, "general")


def _build_system_prompt(mode: str, context: str) -> str:
    return {
        "schedule": schedule_prompt,
        "tutor": tutor_prompt,
        "study": study_prompt,
        "general": general_prompt,
    }[mode](context)


class MessageRouter:
    def __init__(self, memory: MemoryStore, lms, model: str):
        self.memory = memory
        self.lms = schoology
        self.ollama = OllamaClient(model=model)

    def _is_allowed(self, update: Update) -> bool:
        """Only respond to the configured chat."""
        if config.ALLOWED_CHAT_ID == 0:
            return True  # No restriction set — allow all during testing
        return update.effective_chat.id == config.ALLOWED_CHAT_ID

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_allowed(update):
            return
        courses = self.memory.get_courses()
        course_list = "\n".join(f"  • {c['title']}" for c in courses) or "  (no courses synced yet)"
        upcoming = self.memory.get_upcoming_assignments(7)
        upcoming_text = "\n".join(
            f"  • {a['title']} — due in {a['days_until_due']} days"
            for a in upcoming[:3]
        ) or "  (no upcoming assignments)"

        msg = (
            "🧠 *LocalMind is online*\n\n"
            f"*Your courses:*\n{course_list}\n\n"
            f"*Coming up:*\n{upcoming_text}\n\n"
            "*Topics:*\n"
            "  📅 Schedule — due dates, priorities\n"
            "  🎓 Tutor — explanations, quizzes\n"
            "  📖 Study — session planning, notes\n"
            "  💬 General — anything else\n\n"
            "Just message the right topic and I'll help."
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def handle_sync(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_allowed(update):
            return
        await update.message.reply_text("🔄 Syncing Schoology...")
        try:
            await self.lms.sync(self.memory)
            courses = self.memory.get_courses()
            assignments = self.memory.get_assignments()
            await update.message.reply_text(
                f"✅ Synced {len(courses)} courses and {len(assignments)} assignments."
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Sync failed: {e}")

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_allowed(update):
            return
        msg = (
            "📖 *LocalMind Help*\n\n"
            "*/start* — Show your courses and upcoming work\n"
            "*/sync* — Re-sync your Schoology data\n"
            "*/help* — This message\n\n"
            "*Topics:*\n"
            "  📅 *Schedule* — 'What's due this week?' / 'What should I work on?'\n"
            "  🎓 *Tutor* — 'Explain integration by parts' / 'Quiz me on WW2'\n"
            "  📖 *Study* — 'I have 2 hours, help me plan' / 'Remember that...'\n"
            "  💬 *General* — Anything else\n\n"
            "Everything runs locally. Zero API costs. No limits."
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self._is_allowed(update):
            return

        message = update.message
        text = message.text.strip()
        chat_id = message.chat_id
        thread_id = message.message_thread_id or 0

        # Detect mode from topic
        mode = _detect_topic_mode(thread_id)

        # Check Ollama is running
        if not await self.ollama.is_available():
            await message.reply_text(
                "❌ Ollama isn't running.\nStart it with: `ollama serve`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Show typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Build context + system prompt
        student_context = self.memory.build_context()
        system_prompt = _build_system_prompt(mode, student_context)

        # Get conversation history for this topic
        history = _get_history(chat_id, thread_id)
        _add_to_history(chat_id, thread_id, "user", text)

        try:
            response = await self.ollama.chat(
                system_prompt=system_prompt,
                messages=_get_history(chat_id, thread_id)
            )
            _add_to_history(chat_id, thread_id, "assistant", response)

            # Update session memory
            self.memory.update_session(
                topic=mode,
                subject=None,
                summary=f"User asked: {text[:80]}"
            )

            # If study mode and user said "remember that", save a note
            if mode == "study" and "remember that" in text.lower():
                note_content = text.lower().replace("remember that", "").strip()
                # Try to guess subject from enrolled courses
                courses = [c["title"] for c in self.memory.get_courses()]
                subject = "General"
                for c in courses:
                    if any(word in text.lower() for word in c.lower().split()):
                        subject = c
                        break
                self.memory.add_study_note(subject, note_content)

            await message.reply_text(response)

        except Exception as e:
            logger.error(f"Error: {e}")
            await message.reply_text(f"❌ Something went wrong: {e}")

    async def send_morning_digest(self, context: ContextTypes.DEFAULT_TYPE):
        """Daily morning reminder pushed to Schedule topic."""
        if config.ALLOWED_CHAT_ID == 0 or config.TOPIC_SCHEDULE == 0:
            return

        upcoming = self.memory.get_upcoming_assignments(days=7)
        overdue = self.memory.get_overdue_assignments()

        if not upcoming and not overdue:
            return

        lines = ["📅 *Good morning! Here's your day:*\n"]

        if overdue:
            lines.append("⚠️ *Overdue:*")
            for a in overdue[:3]:
                lines.append(f"  • {a['title']} ({a.get('course', '')})")

        if upcoming:
            lines.append("\n📌 *Coming up:*")
            for a in upcoming[:5]:
                d = a["days_until_due"]
                label = "today" if d == 0 else f"in {d} day{'s' if d != 1 else ''}"
                lines.append(f"  • {a['title']} — {label}")

        await context.bot.send_message(
            chat_id=config.ALLOWED_CHAT_ID,
            message_thread_id=config.TOPIC_SCHEDULE,
            text="\n".join(lines),
            parse_mode=ParseMode.MARKDOWN
        )
