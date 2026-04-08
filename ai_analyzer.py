import os
import json
from google import genai
from google.genai import types
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from logger import logger

async def analyze_news_with_llm(articles: list) -> dict:
    """Yeni haberleri alır, Gemini'a gönderir ve JSON formatında yapılandırılmış yanıt döner."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY bulunamadı!")
        return {}
        
    if not articles:
        return {}

    # Yeni nesil google-genai kütüphanesi istemcisi
    client = genai.Client(api_key=api_key)

    # Prompt için verileri hazırla
    news_text = ""
    for idx, article in enumerate(articles, 1):
        news_text += f"Haber {idx}:\nBaşlık: {article['title']}\nÖzet: {article['summary']}\nLink: {article['link']}\n\n"

    system_instruction = """Sen uzman bir yapay zeka araştırmacısı ve yazılım mimarısın. 
Sana verilen AI dünyasındaki son 24 saatin haberlerini analiz et ve SADECE geçerli bir JSON çıktısı üret.
Görevlerin:
1. Verilen haberlerden SADECE yapay zeka/yazılım geliştirenler için en heyecan verici/önemli max 5 tanesini seç.
2. Her gelişmeyi teknik ama akılcı ve akıcı bir Türkçe ile kısaca özetle.
3. Her gelişme için yazılımcılara yönelik "Bu modelle nasıl bir AI wrapper yapılır?", "Hangi veri setiyle fine-tune edilmeli?" gibi somut, uygulanabilir bir proje fikri üret.

Format (Sadece objeler olacak şekilde tam bir JSON üret):
{
  "haberler": [
    {
      "baslik": "Haberin Orijinal Başlığı",
      "ozet": "Özet metni buraya",
      "link": "Orijinal Link buraya",
      "proje_fikri": "Somut proje fikri buraya"
    }
  ]
}
"""

    # Hata anında (özellikle 503 High Demand) bekleyip tekrar denemesi için özel fonksiyon
    @retry(
        wait=wait_exponential(multiplier=2, min=4, max=15), 
        stop=stop_after_attempt(4),
        reraise=True
    )
    async def call_gemini():
        logger.info("LLM (Gemini) API'sine istek atılıyor...")
        return await client.aio.models.generate_content(
            model="gemini-3-flash-preview",  # Gemini 3 Flash - En yeni nesil!
            contents=news_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )

    try:
        response = await call_gemini()
        
        result_content = response.text
        result_json = json.loads(result_content)
        
        logger.info("LLM (Gemini) analizi başarılı.")
        return result_json
        
    except json.JSONDecodeError as e:
        logger.error(f"LLM çıktısı JSON olarak çözülemedi: {e}")
        return {}
    except Exception as e:
        logger.error(f"LLM (Gemini) API Hatası: {e}")
        return {}
