"""
Ollama client — sends prompts to your local model
Talks to localhost:11434, zero external calls
"""

import aiohttp
import json


class OllamaClient:
    def __init__(self, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    async def chat(self, system_prompt: str, messages: list, stream: bool = False) -> str:
        """Send a chat request to Ollama and return the response text."""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_ctx": 4096
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["message"]["content"]
                else:
                    text = await resp.text()
                    raise Exception(f"Ollama error {resp.status}: {text}")

    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return resp.status == 200
        except Exception:
            return False
