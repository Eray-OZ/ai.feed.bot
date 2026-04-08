# AI Feed Bot — Architecture & Code Walkthrough

A fully asynchronous Telegram bot that automatically fetches AI news from RSS feeds, summarizes and ranks them using the **Gemini API**, and delivers a clean daily digest directly to your Telegram account.

---

## High-Level Flow

```
RSS Feeds ──► rss_parser.py ──► ai_analyzer.py ──► notifier.py ──► Telegram
                  │                                        │
            state_manager.py                       state_manager.py
           (filter seen URLs)                     (mark URLs as seen)
```

The pipeline is triggered in two ways:
1. **Automatically** — every day at **09:00 (Istanbul time)** via APScheduler.
2. **Manually** — by sending `/news` to the bot in Telegram.

---

## Module Breakdown

### `main.py` — Entry Point & Orchestrator

This is the application's entry point. It:

- Loads environment variables from `.env` (`TELEGRAM_TOKEN`, `CHAT_ID`, `RSS_URLS`).
- Initializes the `aiogram` Bot and Dispatcher instances.
- Defines `news_workflow()` — the core pipeline function that chains all three stages (fetch → analyze → send).
- Registers the `/news` Telegram command handler, which guards against unauthorized users by comparing `message.chat.id` with the `CHAT_ID` from `.env`.
- Starts the APScheduler (for automatic scheduling) alongside the aiogram polling loop.

```python
async def news_workflow():
    new_articles = await fetch_and_filter_news(RSS_URLS)   # Stage 1
    analyzed_news_json = await analyze_news_with_llm(new_articles)  # Stage 2
    await send_news_to_telegram(bot, CHAT_ID, analyzed_news_json, mark_as_seen)  # Stage 3
```

---

### `rss_parser.py` — RSS Fetcher & Filter

**Function:** `fetch_and_filter_news(rss_urls: list) -> list`

Responsibilities:
- Iterates over each RSS URL provided in `.env`.
- Makes HTTP GET requests with a **browser-like `User-Agent` header** to bypass bot-blocking on sites like TechCrunch.
- Parses the raw response with `feedparser`.
- Filters articles to only include those published within the **last 24 hours** using `published_parsed` (a `struct_time` object converted to a Unix timestamp).
- Cross-checks each article's URL against the **seen news set** loaded from `state_manager`, skipping any already-delivered articles.
- Truncates `summary` fields to **500 characters** to keep prompts manageable.

**Key detail:** Articles without a publication date are included anyway (rare edge case).

---

### `ai_analyzer.py` — Gemini LLM Analyzer

**Function:** `analyze_news_with_llm(articles: list) -> dict`

Responsibilities:
- Formats all fetched articles into a numbered plain-text block and sends it to the **Gemini API** (`gemini-3-flash-preview` model).
- Uses a detailed **system instruction** that instructs Gemini to act as an AI researcher and:
  1. Pick the **top 5 most exciting** articles for developers.
  2. Summarize each in fluent Turkish.
  3. Generate a **concrete project idea** for each article (e.g., "Build a wrapper API using this model").
- Requests a structured **JSON response** via `response_mime_type="application/json"`, eliminating the need for post-processing.
- Wraps the API call in a **`@retry` decorator** (via `tenacity`):
  - Exponential backoff: waits 4–15 seconds between retries.
  - Max 4 attempts (handles `503 High Demand` errors gracefully).

**Expected output JSON shape:**
```json
{
  "haberler": [
    {
      "baslik": "Original News Title",
      "ozet": "Turkish summary...",
      "link": "https://...",
      "proje_fikri": "Concrete project idea..."
    }
  ]
}
```

---

### `notifier.py` — Telegram Message Sender

**Function:** `send_news_to_telegram(bot, chat_id, news_data, mark_seen_callback)`

Responsibilities:
- Iterates over the `haberler` list from the JSON returned by Gemini.
- **HTML-escapes** all text fields (title, summary, project idea) to prevent Telegram parse errors.
- Formats each item into a rich Telegram message using HTML parse mode:
  ```
  🚀 New Development: <title>
  📝 Summary: <summary>
  🔗 Article: <link>
  💡 Project Idea: <project idea>
  ```
- Sends the message using `bot.send_message()` with `ParseMode.HTML`.
- **Only after a successful send**, it calls `mark_seen_callback(link)` to persist the article URL — ensuring no re-delivery even after a bot restart.

---

### `state_manager.py` — Persistence Layer

Tracks which article URLs have already been sent by reading/writing a local `seen_news.json` file.

| Function | Description |
|---|---|
| `load_seen_news()` | Reads `seen_news.json` and returns a Python `set` of URLs. Returns an empty set if the file doesn't exist. |
| `save_seen_news(seen_set)` | Serializes the `set` to a JSON list and writes it to disk asynchronously. |
| `mark_as_seen(link)` | Convenience wrapper: loads → adds → saves. Called after each successful Telegram send. |

All file I/O is **non-blocking**, using `aiofiles` for async reads/writes.

---

### `scheduler.py` — APScheduler Setup

**Function:** `setup_scheduler(job_function) -> AsyncIOScheduler`

- Creates an `AsyncIOScheduler` set to the `Europe/Istanbul` timezone.
- Schedules `news_workflow` as a **cron job** at `hour=9, minute=0` (09:00 daily).
- Uses `replace_existing=True` so re-registering the job on restart doesn't cause duplicates.
- Returns the configured scheduler object (started in `main.py`).

---

### `logger.py` — Centralized Logger

Sets up a single named logger (`ai_news_bot`) with:
- `INFO` log level.
- A `StreamHandler` that writes to `stdout`.
- A format of: `TIMESTAMP - ai_news_bot - LEVEL - message`
- A guard (`if not logger.handlers`) to prevent duplicate log entries when modules import from each other.

Imported and used in every other module as:
```python
from logger import logger
logger.info("...")
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────┐
│                  main.py                    │
│  ┌──────────┐   ┌───────────┐              │
│  │Scheduler │   │ /news cmd │              │
│  │ 09:00/d  │   │  handler  │              │
│  └────┬─────┘   └─────┬─────┘              │
│       └───────┬────────┘                   │
│               ▼                            │
│        news_workflow()                     │
└───────────────┼────────────────────────────┘
                │
    ┌───────────▼───────────┐
    │    rss_parser.py      │  ← fetches & deduplicates
    │  fetch_and_filter_news│  ← filters last 24h articles
    └───────────┬───────────┘
                │  List[{title, link, summary}]
    ┌───────────▼───────────┐
    │   ai_analyzer.py      │  ← sends to Gemini API
    │  analyze_news_with_llm│  ← retries on failure
    └───────────┬───────────┘
                │  {haberler: [...]}
    ┌───────────▼───────────┐
    │     notifier.py       │  ← formats & sends to Telegram
    │  send_news_to_telegram│  ← marks each URL as seen
    └───────────────────────┘
```

---

## Environment Variables (`.env`)

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Your bot's token from [@BotFather](https://t.me/botfather) |
| `CHAT_ID` | Your personal or group chat ID (only this ID can use the bot) |
| `RSS_URLS` | Comma-separated list of RSS feed URLs to monitor |
| `GEMINI_API_KEY` | API key from [Google AI Studio](https://aistudio.google.com) |

---

## Deployment

The bot is configured for **Railway** deployment:

- **`Procfile`**: Defines the start command (`python main.py`).
- **`railway.toml`**: Railway-specific build/run configuration.
- The bot runs 24/7 as a single long-lived asyncio process — the scheduler and the Telegram polling loop run **concurrently** within the same event loop.
