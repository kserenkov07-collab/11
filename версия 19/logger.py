"""
Модуль логирования приложения.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from config import config

class LessVerboseFilter(logging.Filter):
    def filter(self, record):
        # Фильтруем повторяющиеся сообщения о загрузке паттернов
        if "Загружено" in record.getMessage() and "паттернов из" in record.getMessage():
            return False
        return True

class GUIHandler(logging.Handler):
    """Обработчик для вывода логов в GUI"""
    def __init__(self, gui_callback=None):
        super().__init__()
        self.gui_callback = gui_callback
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
    
    def set_gui_callback(self, callback):
        """Установка callback-функции для обновления GUI"""
        self.gui_callback = callback
    
    def emit(self, record):
        try:
            msg = self.format(record)
            if self.gui_callback:
                self.gui_callback(msg)
        except Exception:
            pass

def setup_logger(gui_callback=None):
    """Настройка системы логирования"""
    # Создаем логгер
    logger = logging.getLogger('WalletScanner')
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Удаляем все существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для вывода в консоль (всегда включаем)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Обработчик для записи в файл
    if config.LOG_TO_FILE:
        log_file = os.path.join(config.LOGS_DIR, 'wallet_scanner.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Обработчик для GUI
    if gui_callback:
        gui_handler = GUIHandler(gui_callback)
        gui_handler.setLevel(logging.INFO)
        logger.addHandler(gui_handler)
    
    # Добавляем фильтр для уменьшения verbosity
    verbose_filter = LessVerboseFilter()
    for handler in logger.handlers:
        handler.addFilter(verbose_filter)
    
    return logger

# Глобальный экземпляр логгера
logger = setup_logger()