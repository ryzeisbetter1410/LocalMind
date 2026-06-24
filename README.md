# 🧠 LocalMind

A fully local, zero-cost student AI assistant via Telegram.  
No API keys. No rate limits. No data leaving your machine.

## Features
- 📅 **Schedule** — auto-syncs your real Schoology assignments and due dates
- 🎓 **Tutor** — subject-aware explanations and quizzes based on your actual courses
- 📖 **Study** — session memory, planning, and note-taking
- 💬 **General** — anything else

Runs entirely on [Ollama](https://ollama.com) (local LLM). Free forever.

---

## Setup

### 1. Install Ollama
Download from [ollama.com](https://ollama.com) then pull a model:
```bash
ollama pull llama3.1:8b
# Lower RAM option:
ollama pull phi3:mini
```

### 2. Clone and install
```bash
git clone https://github.com/yourusername/localmind
cd localmind
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env with your values
```

You need:
- **Telegram bot token** — create a bot via [@BotFather](https://t.me/BotFather)
- **Schoology API key** — go to `yourschool.schoology.com/api`

### 4. Set up Telegram Topics
1. Create a Telegram group
2. Go to Group Settings → Topics → Enable Topics
3. Create 4 topics: `Schedule`, `Tutor`, `Study`, `General`
4. Right-click each topic → Copy Link → grab the ID from the URL
5. Paste the IDs into your `.env` file

### 5. Run
```bash
python start.py
```

---

## Project structure
```
localmind/
├── start.py          # Entry point
├── config.py         # Config loader
├── .env.example      # Config template
├── core/
│   ├── ollama.py     # Ollama client
│   ├── prompts.py    # System prompts per topic
│   └── router.py     # Telegram message router
├── schoology/
│   └── client.py     # Schoology API integration
└── memory/
    └── store.py      # Local JSON memory
```

---

## Commands
| Command | What it does |
|---|---|
| `/start` | Show your courses and upcoming work |
| `/sync` | Re-sync Schoology |
| `/help` | Help message |

---

## Stack
- **Python** — core language
- **Ollama** — local LLM inference (Llama 3.1, Phi-3, Mistral, etc.)
- **python-telegram-bot** — Telegram interface
- **Schoology API** — real assignment/course data
- **JSON** — local memory, no database needed

Built as an open source portfolio project. Zero cloud dependencies.
