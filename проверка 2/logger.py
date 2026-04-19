"""
Модуль для логирования действий программы.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from config import Config

def setup_logger():
    """Настройка системы логирования"""
    # Создаем логгер
    logger = logging.getLogger('WalletScanner')
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Обработчик для записи в файл
    if Config.LOG_TO_FILE:
        # Создаем директорию для логов, если ее нет
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Глобальный экземпляр логгера
logger = setup_logger()
