# 🧠 LocalMind

A fully local, free student AI assistant that runs on your own computer via Telegram.  
No API costs. No rate limits. No data leaving your machine. Ever.

**Works with Canvas and Schoology.**

---

## What it does

- 📅 **Schedule** — asks your real Canvas/Schoology account for assignments and due dates automatically
- 🎓 **Tutor** — explains concepts based on your actual enrolled courses
- 📖 **Study** — helps you plan sessions, takes notes, remembers what you worked on
- 💬 **General** — anything else

---

## Before you start

You need three things installed on your computer:

- [Python](https://python.org/downloads) (3.10 or higher)
- [Git](https://git-scm.com/downloads)
- [Ollama](https://ollama.com) (runs the AI model locally)

---

## Installation

### Step 1 — Download Ollama and pull a model

Download Ollama from [ollama.com](https://ollama.com) and install it. Then open a terminal and run:

```bash
ollama pull phi3:mini
```

> **Not sure which model to use?**
> - 8GB RAM or less → `phi3:mini` (fast, lightweight)
> - More than 8GB → `llama3.1:8b` (smarter, slower)

---

### Step 2 — Clone the repo

```bash
git clone https://github.com/ryzeisbetter1410/localmind.git
cd localmind
```

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
pip install "python-telegram-bot[job-queue]"
```

---

### Step 4 — Create your config file

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in the following:

**Telegram bot token** — message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow the steps, copy the token it gives you.

**Canvas token** (if your school uses Canvas) — go to Canvas → Account → Settings → scroll down to Approved Integrations → click **New Access Token** → copy it.

**Schoology keys** (if your school uses Schoology) — go to `yourschool.schoology.com/api` → your consumer key and secret are right there.

You only need one — Canvas or Schoology, not both.

---

### Step 5 — Set up Telegram Topics

1. Create a new Telegram group
2. Go to the group → Settings → Topics → turn on Topics
3. Create 4 topics named: `Schedule`, `Tutor`, `Study`, `General`
4. To get a topic's ID: right-click the topic → Copy Link → the number at the end of the URL is the ID
5. Paste those 4 IDs into your `.env` file

---

### Step 6 — Run it

```bash
python start.py
```

If you see `✅ LocalMind is live` — you're good. Message your bot in Telegram.

---

## Commands

| Command | What it does |
|---|---|
| `/start` | Show your courses and upcoming assignments |
| `/sync` | Re-sync your Canvas or Schoology data |
| `/help` | Show help |

---

## Project structure

```
localmind/
├── start.py            # Run this
├── config.py           # Loads your .env
├── .env.example        # Config template
├── core/
│   ├── ollama.py       # Talks to your local model
│   ├── prompts.py      # AI personality per topic
│   └── router.py       # Routes Telegram messages
├── canvas/
│   └── client.py       # Canvas API integration
├── schoology/
│   └── client.py       # Schoology API integration
└── memory/
    └── store.py        # Saves everything locally as JSON
```

---

## Still stuck?

Paste this into [Claude](https://claude.ai) and describe your problem:

```
I am trying to set up LocalMind, a local student AI assistant that runs on Ollama and connects to Telegram.
Here is the full project: https://github.com/ryzeisbetter1410/localmind

Here is what I have done so far:
- Installed Python, Git, and Ollama
- Cloned the repo and ran pip install -r requirements.txt
- Filled in my .env file with my Telegram token and LMS credentials
- Created a Telegram group with 4 topics (Schedule, Tutor, Study, General)

Here is the error I am getting:
[paste your error here]

My operating system is: [Windows / Mac / Linux]
My Python version is: [run python --version]
My Ollama model is: [phi3:mini / llama3.1:8b]

Please help me debug this step by step.
```

---

Built by [@ryzeisbetter1410](https://github.com/ryzeisbetter1410). Open source. Zero cloud dependencies.