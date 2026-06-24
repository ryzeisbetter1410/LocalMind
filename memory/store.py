"""
Memory store — persists everything to local JSON
No database needed. All data stays on your machine.
"""

import json
import os
from datetime import datetime
from typing import Any


MEMORY_FILE = "memory.json"

DEFAULT_MEMORY = {
    "courses": [],
    "assignments": [],
    "last_session": {
        "topic": None,
        "subject": None,
        "summary": None,
        "timestamp": None
    },
    "study_notes": {},
    "synced_at": None
}


class MemoryStore:
    def __init__(self, path: str = MEMORY_FILE):
        self.path = path
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return DEFAULT_MEMORY.copy()

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    # ── Courses ───────────────────────────────────────

    def set_courses(self, courses: list):
        self._data["courses"] = courses
        self._save()

    def get_courses(self) -> list:
        return self._data.get("courses", [])

    # ── Assignments ───────────────────────────────────

    def set_assignments(self, assignments: list):
        self._data["assignments"] = assignments
        self._save()

    def get_assignments(self) -> list:
        return self._data.get("assignments", [])

    def get_upcoming_assignments(self, days: int = 7) -> list:
        """Return assignments due within the next N days, sorted by due date."""
        now = datetime.now()
        upcoming = []
        for a in self._data.get("assignments", []):
            due = a.get("due_date")
            if not due:
                continue
            try:
                due_dt = datetime.fromisoformat(due)
                delta = (due_dt - now).days
                if 0 <= delta <= days:
                    upcoming.append({**a, "days_until_due": delta})
            except Exception:
                continue
        return sorted(upcoming, key=lambda x: x["days_until_due"])

    def get_overdue_assignments(self) -> list:
        now = datetime.now()
        overdue = []
        for a in self._data.get("assignments", []):
            due = a.get("due_date")
            if not due:
                continue
            try:
                due_dt = datetime.fromisoformat(due)
                if due_dt < now:
                    overdue.append(a)
            except Exception:
                continue
        return overdue

    # ── Session Memory ────────────────────────────────

    def update_session(self, topic: str, subject: str = None, summary: str = None):
        self._data["last_session"] = {
            "topic": topic,
            "subject": subject,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        self._save()

    def get_last_session(self) -> dict:
        return self._data.get("last_session", {})

    # ── Study Notes ───────────────────────────────────

    def add_study_note(self, subject: str, note: str):
        if subject not in self._data["study_notes"]:
            self._data["study_notes"][subject] = []
        self._data["study_notes"][subject].append({
            "note": note,
            "timestamp": datetime.now().isoformat()
        })
        self._save()

    def get_study_notes(self, subject: str) -> list:
        return self._data.get("study_notes", {}).get(subject, [])

    # ── Sync metadata ─────────────────────────────────

    def set_synced_at(self):
        self._data["synced_at"] = datetime.now().isoformat()
        self._save()

    def get_synced_at(self) -> str:
        return self._data.get("synced_at", "Never")

    # ── Context builder ───────────────────────────────

    def build_context(self) -> str:
        """Build a context string to inject into every Ollama prompt."""
        courses = [c.get("title", "") for c in self.get_courses()]
        upcoming = self.get_upcoming_assignments(days=7)
        last = self.get_last_session()

        lines = ["=== STUDENT CONTEXT ==="]

        if courses:
            lines.append(f"Enrolled courses: {', '.join(courses)}")

        if upcoming:
            lines.append("Upcoming assignments (next 7 days):")
            for a in upcoming[:5]:
                lines.append(f"  - {a['title']} ({a.get('course','')}) due in {a['days_until_due']} days")

        if last.get("summary"):
            lines.append(f"Last session: {last['summary']} (topic: {last.get('topic','?')})")

        lines.append("======================")
        return "\n".join(lines)
