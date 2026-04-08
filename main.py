import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from logger import logger
from rss_parser import fetch_and_filter_news
from ai_analyzer import analyze_news_with_llm
from notifier import send_news_to_telegram
from state_manager import mark_as_seen
from scheduler import setup_scheduler

# .env dosyasındaki değişkenleri yükle
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RSS_URLS_RAW = os.getenv("RSS_URLS", "")

# Virgülle ayrılmış URL'leri listeye çevir
RSS_URLS = [url.strip() for url in RSS_URLS_RAW.split(",") if url.strip()]

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

async def news_workflow():
    """Tüm haber çekme, analiz etme ve gönderme döngüsünü içeren ana iş akışı."""
    logger.info("Haber iş akışı başlatılıyor...")
    try:
        # 1. Haberi çek ve filtrele
        new_articles = await fetch_and_filter_news(RSS_URLS)
        
        if not new_articles:
            logger.info("Analiz edilecek yeni haber yok.")
            return

        # 2. LLM analizi yap
        analyzed_news_json = await analyze_news_with_llm(new_articles)
        
        # 3. Telegram'a gönder
        if analyzed_news_json:
            await send_news_to_telegram(bot, CHAT_ID, analyzed_news_json, mark_as_seen)
        else:
            logger.warning("LLM analizi boş döndü veya hata oluştu.")
            
    except Exception as e:
        logger.error(f"İş akışı sırasında beklenmeyen hata: {e}")
        
    logger.info("Haber iş akışı tamamlandı.")

@dp.message(Command("news"))
async def cmd_news(message: Message):
    """Manuel olarak süreci tetiklemek için /news komutu."""
    # Sadece yetkili kişinin (.env'deki CHAT_ID) komutlarını kabul et
    if str(message.chat.id) != str(CHAT_ID):
        await message.answer("You are not authorized to use this bot.")
        return
        
    await message.answer("Fetching and analyzing the latest AI news... Please wait.")
    # Arka planda workflow'u başlat
    asyncio.create_task(news_workflow())

async def main():
    if not TELEGRAM_TOKEN or not CHAT_ID or not RSS_URLS:
        logger.error("Lütfen .env dosyasında TELEGRAM_TOKEN, CHAT_ID ve RSS_URLS tanımlamalarını yapın.")
        return

    import sys
    if "--cron" in sys.argv:
        logger.info("Bot cron modunda başlatıldı. Görev 1 kez çalıştırılıp kapanacak...")
        await news_workflow()
        await bot.session.close()
        return

    logger.info("Bot polling modunda başlatılıyor...")
    
    # Zamanlayıcıyı kur ve başlat (sadece local/sürekli açık sunucular için)
    scheduler = setup_scheduler(news_workflow)
    scheduler.start()
    
    # Aiogram bot döngüsünü başlat (Komutları dinlemek için)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Polling hatası: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot durduruldu.")
