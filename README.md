# AI Feed Bot

An autonomous Telegram bot that monitors the AI world, curates the most important developments from the last 24 hours, summarizes them using Gemini 3 Flash, and delivers a daily digest straight to your Telegram chat.

## Features

- Scans multiple RSS feeds (TechCrunch AI, VentureBeat, Reddit, and more)
- Filters articles published within the last 24 hours
- Prevents duplicate notifications via a local state file (`seen_news.json`)
- Uses Gemini 3 Flash to generate summaries and actionable project ideas for each story
- Runs automatically every day at 09:00 (Europe/Istanbul)
- Supports on-demand reports via the `/news` Telegram command (restricted to the configured Chat ID)

## Project Structure

```
.
├── main.py           # Entry point, bot startup, command handlers
├── rss_parser.py     # RSS fetching and 24-hour filtering
├── ai_analyzer.py    # Gemini LLM integration and JSON output
├── notifier.py       # Telegram message formatting and delivery
├── scheduler.py      # APScheduler daily job setup
├── state_manager.py  # Seen news persistence (seen_news.json)
├── logger.py         # Centralized logging configuration
├── requirements.txt
├── .env.example
└── .env.example
```

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in your credentials in .env
python main.py
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | Bot token obtained from BotFather |
| `CHAT_ID` | Your personal Telegram user ID 
| `GEMINI_API_KEY` | Google AI Studio API key |
| `RSS_URLS` | Comma-separated list of RSS feed URLs |

## Serverless Deployment (GitHub Actions)

1. Push this repository to GitHub.
2. Go to your repository settings on GitHub: **Settings > Secrets and variables > Actions**.
3. Create a **New repository secret** for each environment variable (`TELEGRAM_TOKEN`, `CHAT_ID`, `GEMINI_API_KEY`, `RSS_URLS`).
4. The bot will automatically wake up, check for news, send you a Telegram digest, and shut down every day at **13:40 (Istanbul Time)** via the `.github/workflows/bot.yml` configuration.
5. *Continuous Integration:* Whenever you push new code to the repository, the next scheduled run will automatically use the freshest code. No server restarts required!

## Tech Stack

- [aiogram 3.x](https://docs.aiogram.dev/) — Async Telegram Bot framework
- [google-genai](https://github.com/google-gemini/generative-ai-python) — Gemini 3 Flash LLM
- [feedparser](https://feedparser.readthedocs.io/) — RSS/Atom feed parser
- [APScheduler](https://apscheduler.readthedocs.io/) — Async job scheduler
- [python-dotenv](https://github.com/theskumar/python-dotenv) — Environment variable management
