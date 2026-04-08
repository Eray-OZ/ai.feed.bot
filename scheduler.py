from apscheduler.schedulers.asyncio import AsyncIOScheduler
from logger import logger

def setup_scheduler(job_function, *args) -> AsyncIOScheduler:
    """Zamanlayıcıyı (scheduler) oluşturur ve varsayılan işi ekler."""
    scheduler = AsyncIOScheduler(timezone="Europe/Istanbul")
    
    # Her gün sabah 09:00'da çalışacak şekilde ayarla
    scheduler.add_job(
        job_function, 
        'cron', 
        hour=9, 
        minute=0, 
        args=args,
        id='daily_news_job',
        replace_existing=True
    )
    
    logger.info("APScheduler her gün 09:00 için ayarlandı.")
    return scheduler
