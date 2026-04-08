import json
import os
import aiofiles
from logger import logger

STATE_FILE = "seen_news.json"

async def load_seen_news() -> set:
    """Kaydedilmiş eski haber linklerini okur ve set olarak döner."""
    if not os.path.exists(STATE_FILE):
        return set()
    
    try:
        async with aiofiles.open(STATE_FILE, mode='r', encoding='utf-8') as f:
            content = await f.read()
            if not content:
                return set()
            data = json.loads(content)
            return set(data)
    except Exception as e:
        logger.error(f"seen_news.json okunamadi: {e}")
        return set()

async def save_seen_news(seen_set: set):
    """Gönderilen haberlerin linklerini JSON formatında kaydeder."""
    try:
        async with aiofiles.open(STATE_FILE, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(list(seen_set), ensure_ascii=False, indent=4))
    except Exception as e:
        logger.error(f"seen_news.json kaydedilemedi: {e}")

async def mark_as_seen(link: str):
    """Tek bir linki görüldü olarak işaretler."""
    seen = await load_seen_news()
    seen.add(link)
    await save_seen_news(seen)
