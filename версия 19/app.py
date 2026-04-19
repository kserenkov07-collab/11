"""
Основной класс приложения.
"""
import threading
import time
from typing import Dict
from config import config
from logger import logger
from crypto_utils import generate_mnemonic, mnemonic_to_seed, derive_addresses, add_checked_mnemonic
from worker_system import OptimizedWorkerManager
from results_manager import ResultsManager

class Application:
    """Основной класс приложения"""
    
    def __init__(self):
        self.is_running = False
        self.start_time = None
        self.checked_count = 0
        self.found_count = 0
        
        # Инициализация модулей
        self.results_manager = ResultsManager()
        self.worker_manager = OptimizedWorkerManager(self.results_manager)
        
        # Callback для обновления UI
        self.ui_callback = None
        
        # Статистика производительности
        self.performance_stats = {
            'start_time': 0,
            'total_checked': 0,
            'total_found': 0,
            'avg_speed': 0,
            'peak_speed': 0,
            'last_update': 0,
            'last_checked': 0
        }
    
    def set_ui_callback(self, callback):
        """Установка callback для обновления UI"""
        self.ui_callback = callback
    
    def start(self):
        """Запуск приложения"""
        if self.is_running:
            return
        
        self.is_running = True
        self.start_time = time.time()
        self.checked_count = 0
        self.found_count = 0
        
        # Инициализация статистики производительности
        self.performance_stats = {
            'start_time': self.start_time,
            'total_checked': 0,
            'total_found': 0,
            'avg_speed': 0,
            'peak_speed': 0,
            'last_update': self.start_time,
            'last_checked': 0
        }
        
        # Запуск менеджера воркеров
        self.worker_manager.start()
        
        # Запуск мониторинга
        self.monitor_thread = threading.Thread(target=self._monitor_workers)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Запуск мониторинга производительности
        self.performance_thread = threading.Thread(target=self._monitor_performance)
        self.performance_thread.daemon = True
        self.performance_thread.start()
        
        logger.info("Приложение запущено")
    
    def stop(self):
        """Остановка приложения"""
        if not self.is_running:
            return
        
        self.is_running = False
        self.worker_manager.stop()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        if self.performance_thread and self.performance_thread.is_alive():
            self.performance_thread.join(timeout=5.0)
        
        logger.info("Приложение остановлено")
    
    def _monitor_workers(self):
        """Мониторинг состояния воркеров"""
        while self.is_running:
            try:
                stats = self.worker_manager.get_stats()
                self.checked_count = stats['checked']
                self.found_count = stats['found']
                
                # Рассчитываем скорость проверки
                current_time = time.time()
                elapsed = current_time - self.performance_stats['last_update']
                
                if elapsed > 0:
                    current_speed = (self.checked_count - self.performance_stats['last_checked']) / elapsed
                    self.performance_stats['avg_speed'] = (
                        self.performance_stats['avg_speed'] * 0.9 + current_speed * 0.1
                    )
                    self.performance_stats['peak_speed'] = max(
                        self.performance_stats['peak_speed'], current_speed
                    )
                
                self.performance_stats['last_update'] = current_time
                self.performance_stats['last_checked'] = self.checked_count
                self.performance_stats['total_checked'] = self.checked_count
                self.performance_stats['total_found'] = self.found_count
                
                if self.ui_callback:
                    self.ui_callback({
                        'type': 'stats',
                        'checked': self.checked_count,
                        'found': self.found_count,
                        'speed': self.performance_stats['avg_speed'],
                        'peak_speed': self.performance_stats['peak_speed'],
                        'queue_size': self.worker_manager.task_queue.qsize() if hasattr(self.worker_manager, 'task_queue') else 0
                    })
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Ошибка мониторинга: {e}")
                time.sleep(5)
    
    def _monitor_performance(self):
        """Мониторинг производительности системы"""
        while self.is_running:
            time.sleep(30)  # Проверяем каждые 30 секунд
            
            try:
                # Анализируем производительность и при необходимости корректируем настройки
                current_time = time.time()
                total_elapsed = current_time - self.performance_stats['start_time']
                
                if total_elapsed > 0:
                    overall_speed = self.checked_count / total_elapsed
                    
                    # Логируем производительность
                    logger.info(
                        f"Производительность: {overall_speed:.1f} кош/сек, "
                        f"Пиковая: {self.performance_stats['peak_speed']:.1f}, "
                        f"Найдено: {self.found_count}"
                    )
                    
                # Динамическая корректировка настроек (опционально)
                if hasattr(config, 'DYNAMIC_WORKER_ADJUSTMENT') and config.DYNAMIC_WORKER_ADJUSTMENT:
                    self._adjust_worker_settings(overall_speed)
                
            except Exception as e:
                logger.error(f"Ошибка мониторинга производительности: {e}")
    
    def _adjust_worker_settings(self, current_speed):
        """Динамическая корректировка настроек воркеров"""
        # Здесь можно реализовать логику динамической настройки
        # Например, увеличение/уменьшение BATCH_SIZE на основе текущей скорости
        pass
    
    def get_stats(self) -> Dict:
        """Получение текущей статистики"""
        return {
            'checked': self.checked_count,
            'found': self.found_count,
            'running_time': time.time() - self.start_time if self.start_time else 0,
            'queue_size': self.worker_manager.task_queue.qsize() if hasattr(self.worker_manager, 'task_queue') else 0,
            'avg_speed': self.performance_stats['avg_speed'],
            'peak_speed': self.performance_stats['peak_speed']
        }
    
    def get_performance_stats(self) -> Dict:
        """Получение расширенной статистики производительности"""
        return self.performance_stats.copy()
    
    def update_settings(self, new_settings: Dict):
        """Обновление настроек приложения"""
        config.update_settings(new_settings)
        
        # Перезапуск воркеров с новыми настройки
        if self.is_running:
            self.stop()
            self.start()