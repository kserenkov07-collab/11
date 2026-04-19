"""
Оптимизированный исполнитель с пулом потоков и приоритезацией.
"""
import concurrent.futures
import threading
from concurrent.futures import ThreadPoolExecutor

class OptimizedExecutor:
    """Оптимизированный исполнитель с пулом потоков и приоритезацией"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(OptimizedExecutor, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.executor = None
        self.max_workers = 100  # Увеличиваем количество рабочих потоков
        self._initialized = True
    
    def start(self):
        """Запуск исполнителя"""
        if self.executor is not None:
            return
            
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="wallet_checker"
        )
    
    def stop(self):
        """Остановка исполнителя"""
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
    
    def submit(self, fn, *args, **kwargs):
        """Добавление задачи в пул"""
        if self.executor is None:
            self.start()
        return self.executor.submit(fn, *args, **kwargs)
    
    def map(self, fn, iterable, timeout=None, chunksize=1):
        """Параллельное выполнение функции для элементов iterable"""
        if self.executor is None:
            self.start()
        return self.executor.map(fn, iterable, timeout=timeout, chunksize=chunksize)

# Глобальный экземпляр
optimized_executor = OptimizedExecutor()
