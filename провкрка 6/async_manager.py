"""
Менеджер для управления асинхронными операциями и циклом событий.
"""
import asyncio
import threading
import time
from functools import wraps

class AsyncManager:
    """Класс для управления асинхронными операциями"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AsyncManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.loop = None
        self._running = False
        self._thread = None
        self._tasks = set()
        self._initialized = True
    
    def start(self):
        """Запуск цикла событий в отдельном потоке"""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        # Ждем инициализации цикла
        while self.loop is None:
            time.sleep(0.1)
    
    def stop(self):
        """Остановка цикла событий"""
        if not self._running:
            return
            
        self._running = False
        if self.loop and self.loop.is_running():
            # Отменяем все задачи
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            
            # Останавливаем цикл
            self.loop.call_soon_threadsafe(self.loop.stop)
        
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
    
    def _run_loop(self):
        """Запуск цикла событий"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_forever()
        finally:
            # Завершаем все оставшиеся задачи
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            
            # Дожидаемся завершения задач
            if pending:
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            self.loop.close()
            self.loop = None
    
    def run_async(self, coro):
        """Запуск корутины в цикле событий"""
        if not self._running or not self.loop:
            raise RuntimeError("AsyncManager не запущен")
        
        # Создаем задачу и добавляем ее в набор
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        task = future._task
        self._tasks.add(task)
        
        # Удаляем задачу после завершения
        task.add_done_callback(lambda t: self._tasks.discard(t))
        
        return future

# Глобальный экземпляр менеджера
async_manager = AsyncManager()

def async_command(func):
    """Декоратор для асинхронных команд"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return async_manager.run_async(func(*args, **kwargs))
    return wrapper
