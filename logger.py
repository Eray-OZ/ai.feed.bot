import logging
import sys

def setup_logger():
    logger = logging.getLogger("ai_news_bot")
    logger.setLevel(logging.INFO)
    
    # Konsola yazdırmak için formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Sadece bir kere eklenmesini sağla (çift loglamayı engeller)
    if not logger.handlers:
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logger()
