import feedparser
import time
import requests
from logger import logger
from state_manager import load_seen_news

async def fetch_and_filter_news(rss_urls: list) -> list:
    """RSS linklerini tarar, son 24 saatin haberlerini süzer ve unseen (yeni) olanları döner."""
    logger.info("RSS feed'leri taranıyor...")
    seen_news = await load_seen_news()
    new_articles = []
    
    current_time = time.time()
    one_day_seconds = 24 * 60 * 60
    
    # Bazı siteler (Techcrunch vb.) botları engellediği için kendimizi gerçek bir tarayıcı gibi gösteriyoruz:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for url in rss_urls:
        url = url.strip()
        if not url:
            continue
            
        try:
            # RSS'i güvenli bir şekilde çekiyoruz
            response = requests.get(url, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries:
                link = entry.get('link', '')
                if not link or link in seen_news:
                    continue
                
                # Tarih bilgisini al (published_parsed genellikle struct_time döner)
                published_parsed = entry.get('published_parsed')
                if published_parsed:
                    entry_time = time.mktime(published_parsed)
                    # Sadece son 24 saatin haberleri
                    if current_time - entry_time <= one_day_seconds:
                        new_articles.append({
                            'title': entry.get('title', 'Başlıksız'),
                            'link': link,
                            'summary': entry.get('summary', '')[:500] # Çok uzunsa diye kırp
                        })
                else:
                    # Tarih yoksa (nadiren olur) yine de ekleyelim
                    new_articles.append({
                        'title': entry.get('title', 'Başlıksız'),
                        'link': link,
                        'summary': entry.get('summary', '')[:500]
                    })
        except Exception as e:
            logger.error(f"RSS Parçalama hatası ({url}): {e}")
            
    logger.info(f"Toplam {len(new_articles)} yeni haber bulundu.")
    return new_articles
