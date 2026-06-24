"""
Canvas LMS API client
Pulls courses and assignments using a personal access token.
No OAuth needed — just one token from Canvas settings.
"""

import aiohttp
from datetime import datetime
from memory.store import MemoryStore


class CanvasClient:
    def __init__(self, token: str, domain: str = "canvas.instructure.com"):
        self.token = token
        self.base_url = f"https://{domain}/api/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def _get(self, endpoint: str, params: dict = None) -> list | dict:
        """Paginated GET — Canvas returns results in pages of 10-100."""
        url = f"{self.base_url}{endpoint}"
        results = []
        async with aiohttp.ClientSession() as session:
            while url:
                async with session.get(url, headers=self.headers, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, list):
                            results.extend(data)
                        else:
                            return data
                        # Follow Canvas pagination via Link header
                        link = resp.headers.get("Link", "")
                        url = None
                        for part in link.split(","):
                            if 'rel="next"' in part:
                                url = part.split(";")[0].strip().strip("<>")
                                params = None  # params already in URL
                                break
                    else:
                        text = await resp.text()
                        raise Exception(f"Canvas API error {resp.status}: {text}")
        return results

    async def get_courses(self) -> list:
        """Fetch all active enrolled courses."""
        try:
            data = await self._get("/courses", params={
                "enrollment_state": "active",
                "per_page": 50
            })
            return [
                {
                    "id": str(c.get("id")),
                    "title": c.get("name", "Unknown"),
                    "course_code": c.get("course_code", ""),
                    "section": ""
                }
                for c in data
                if not c.get("access_restricted_by_date", False)
            ]
        except Exception as e:
            print(f"⚠️  Could not fetch Canvas courses: {e}")
            return []

    async def get_assignments(self, course_id: str, course_title: str) -> list:
        """Fetch assignments for a course."""
        try:
            data = await self._get(f"/courses/{course_id}/assignments", params={
                "per_page": 50,
                "order_by": "due_at"
            })
            result = []
            for a in data:
                due_raw = a.get("due_at")
                due_dt = None
                if due_raw:
                    try:
                        due_dt = datetime.fromisoformat(due_raw.replace("Z", "+00:00")).isoformat()
                    except Exception:
                        due_dt = due_raw
                result.append({
                    "id": str(a.get("id")),
                    "title": a.get("name", "Untitled"),
                    "due_date": due_dt,
                    "description": a.get("description", ""),
                    "course": course_title,
                    "section_id": course_id,
                    "max_points": a.get("points_possible", 0),
                    "submission_types": a.get("submission_types", [])
                })
            return result
        except Exception as e:
            print(f"⚠️  Could not fetch assignments for {course_title}: {e}")
            return []

    async def sync(self, memory: MemoryStore):
        """Full sync — pull all courses and assignments into memory."""
        courses = await self.get_courses()
        memory.set_courses(courses)

        all_assignments = []
        for course in courses:
            assignments = await self.get_assignments(course["id"], course["title"])
            all_assignments.extend(assignments)

        memory.set_assignments(all_assignments)
        memory.set_synced_at()
