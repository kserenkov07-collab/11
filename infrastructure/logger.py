import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def get_logger(name: str = 'MetaHunter') -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console = logging.StreamHandler(sys.stdout)
    # Попробуем переключить консоль на UTF-8
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    console.setFormatter(formatter)
    logger.addHandler(console)

    log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'meta_hunter.log'),
        maxBytes=10*1024*1024, backupCount=5,
        encoding='utf-8'  # явно укажем кодировку
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
