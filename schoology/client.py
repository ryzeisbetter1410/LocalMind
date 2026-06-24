"""
Schoology API client
Pulls your real courses and assignments using OAuth 1.0
"""

import time
import hmac
import hashlib
import random
import string
import urllib.parse
import aiohttp
from datetime import datetime
from memory.store import MemoryStore


class SchoologyClient:
    def __init__(self, consumer_key: str, consumer_secret: str, domain: str = "app.schoology.com"):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.base_url = f"https://api.schoology.com/v1"
        self.domain = domain

    def _oauth_header(self, method: str, url: str, token: str = "", token_secret: str = "") -> str:
        """Build OAuth 1.0 PLAINTEXT authorization header."""
        nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        timestamp = str(int(time.time()))

        signature = f"{urllib.parse.quote(self.consumer_secret, safe='')}&{urllib.parse.quote(token_secret, safe='')}"

        header = (
            f'OAuth realm="Schoology API",'
            f'oauth_consumer_key="{self.consumer_key}",'
            f'oauth_token="{token}",'
            f'oauth_nonce="{nonce}",'
            f'oauth_timestamp="{timestamp}",'
            f'oauth_signature_method="PLAINTEXT",'
            f'oauth_version="1.0",'
            f'oauth_signature="{signature}"'
        )
        return header

    async def _get(self, endpoint: str) -> dict:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": self._oauth_header("GET", url),
            "Content-Type": "application/json"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    text = await resp.text()
                    raise Exception(f"Schoology API error {resp.status}: {text}")

    async def get_courses(self) -> list:
        """Fetch all enrolled courses."""
        try:
            data = await self._get("/sections?limit=50")
            sections = data.get("section", [])
            return [
                {
                    "id": s.get("id"),
                    "title": s.get("course_title", s.get("section_title", "Unknown")),
                    "section": s.get("section_title", ""),
                    "course_code": s.get("course_code", "")
                }
                for s in sections
            ]
        except Exception as e:
            print(f"⚠️  Could not fetch courses: {e}")
            return []

    async def get_assignments(self, section_id: str) -> list:
        """Fetch assignments for a specific course section."""
        try:
            data = await self._get(f"/sections/{section_id}/assignments?limit=50")
            assignments = data.get("assignment", [])
            result = []
            for a in assignments:
                due_raw = a.get("due", "")
                due_dt = None
                if due_raw:
                    try:
                        due_dt = datetime.fromisoformat(due_raw.replace("Z", "+00:00")).isoformat()
                    except Exception:
                        due_dt = due_raw
                result.append({
                    "id": a.get("id"),
                    "title": a.get("title", "Untitled"),
                    "due_date": due_dt,
                    "description": a.get("description", ""),
                    "section_id": section_id,
                    "max_points": a.get("max_points", 0)
                })
            return result
        except Exception as e:
            print(f"⚠️  Could not fetch assignments for section {section_id}: {e}")
            return []

    async def sync(self, memory: MemoryStore):
        """Full sync — pull all courses and their assignments into memory."""
        courses = await self.get_courses()
        memory.set_courses(courses)

        all_assignments = []
        for course in courses:
            assignments = await self.get_assignments(course["id"])
            # Tag each assignment with course title
            for a in assignments:
                a["course"] = course["title"]
            all_assignments.extend(assignments)

        memory.set_assignments(all_assignments)
        memory.set_synced_at()
