from aiogram import Bot
from aiogram.enums import ParseMode
import html
from logger import logger

async def send_news_to_telegram(bot: Bot, chat_id: str, news_data: dict, mark_seen_callback):
    """LLM'den gelen JSON verisini HTML formatlayarak Telegram'a atar ve linki seen olarak işaretler."""
    if not news_data or "haberler" not in news_data:
        return
        
    haberler = news_data.get("haberler", [])
    if not haberler:
        logger.info("Gönderilecek yeni haber bulunamadı.")
        return

    logger.info(f"{len(haberler)} adet haber Telegram'a gönderilecek.")

    for haber in haberler:
        # LLM'den gelen verileri güvenli şekilde HTML escape yapıyoruz
        baslik = html.escape(haber.get("baslik", "Başlık Yok"))
        ozet = html.escape(haber.get("ozet", "Özet Yok"))
        link = haber.get("link", "#")
        proje_fikri = html.escape(haber.get("proje_fikri", "Fikir üretilemedi."))
        
        message_text = (
            f"🚀 <b>Yeni Gelişme:</b> {baslik}\n"
            f"📝 <b>Özet:</b> {ozet}\n"
            f"🔗 <b>Makale:</b> <a href='{link}'>Okumak için tıkla</a>\n"
            f"💡 <b>Proje Fikri:</b> <i>{proje_fikri}</i>"
        )
        
        try:
            await bot.send_message(
                chat_id=chat_id, 
                text=message_text, 
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False
            )
            logger.info(f"Haber başarıyla gönderildi: {baslik}")
            
            # Gönderim başarılıysa seen_news'e ekle
            if link and link != "#":
                await mark_seen_callback(link)
                
        except Exception as e:
            logger.error(f"Telegram'a haber gönderilirken hata: {e}")
