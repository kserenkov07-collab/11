"""
Модуль для логирования действий программы.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from config import Config

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
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Удаляем все существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для вывода в консоль (только если не в режиме .pyw)
    if not hasattr(sys, 'executable') or not sys.executable.endswith('pythonw.exe'):
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
    
    # Обработчик для GUI
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
