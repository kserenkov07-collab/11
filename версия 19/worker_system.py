"""
Система управления воркерами с многопоточностью.
"""
import asyncio
import concurrent.futures
import queue
import threading
import time
import hashlib
import os
from typing import Dict, List, Set
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from config import config
from logger import logger
from crypto_utils import generate_mnemonic, mnemonic_to_seed, derive_addresses, add_checked_mnemonic, is_mnemonic_checked

@dataclass
class WorkerTask:
    mnemonic: str
    addresses: Dict[str, str]
    priority: float = 1.0
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()

class WorkerHealthMonitor:
    """Мониторинг здоровья воркеров с минимальными блокировками"""
    
    def __init__(self):
        self.worker_stats = {}
        self.lock = threading.RLock()
        self.healthy_workers: Set[int] = set()
    
    def record_metrics(self, worker_id: int, worker_type: str, success: bool, processing_time: float):
        """Запись метрик воркера с минимальной блокировкой"""
        key = f"{worker_type}_{worker_id}"
        
        with self.lock:
            if key not in self.worker_stats:
                self.worker_stats[key] = {
                    'success_count': 0, 'error_count': 0, 
                    'total_time': 0.0, 'avg_time': 0.0
                }
            
            stats = self.worker_stats[key]
            if success:
                stats['success_count'] += 1
            else:
                stats['error_count'] += 1
            
            stats['total_time'] += processing_time
            stats['avg_time'] = stats['total_time'] / (stats['success_count'] + stats['error_count'])
            
            # Определяем здоровье воркера
            error_ratio = stats['error_count'] / max(1, stats['success_count'] + stats['error_count'])
            if error_ratio < 0.1:  # Меньше 10% ошибок
                self.healthy_workers.add(worker_id)
            else:
                self.healthy_workers.discard(worker_id)

class OptimizedPriorityQueue:
    """Высокопроизводительная приоритетная очередь"""
    
    def __init__(self, maxsize: int = 10000):
        self.queue = queue.PriorityQueue(maxsize=maxsize)
        self.lock = threading.Lock()
        self.size = 0
    
    def put(self, priority: float, item) -> bool:
        """Добавление элемента в очередь"""
        with self.lock:
            if self.size >= self.queue.maxsize:
                return False
            
            try:
                self.queue.put((-priority, time.time(), item))  # Negative priority for max heap
                self.size += 1
                return True
            except queue.Full:
                return False
    
    def get(self, timeout: float = 1.0):
        """Получение элемента из очереди"""
        try:
            priority, timestamp, item = self.queue.get(timeout=timeout)
            with self.lock:
                self.size -= 1
            return -priority, item  # Convert back to positive priority
        except queue.Empty:
            raise queue.Empty
    
    def qsize(self) -> int:
        """Текущий размер очереди"""
        with self.lock:
            return self.size

class MnemonicGeneratorWorker:
    """Специализированный воркер для генерации мнемонических фраз"""
    
    def __init__(self, worker_id: int, output_queue: OptimizedPriorityQueue):
        self.worker_id = worker_id
        self.output_queue = output_queue
        self.is_running = False
        self.thread = None
        self.generated_count = 0
    
    def start(self):
        """Запуск воркера"""
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name=f"MnemGen-{self.worker_id}")
        self.thread.start()
    
    def stop(self):
        """Остановка воркера"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
    
    def _run(self):
        """Основной цикл работы воркера"""
        batch_size = min(100, config.BATCH_SIZE)
        
        while self.is_running:
            try:
                # Генерируем пакет мнемонических фраз
                mnemonics = []
                for _ in range(batch_size):
                    try:
                        mnemonic = generate_mnemonic()
                        if not is_mnemonic_checked(mnemonic):
                            mnemonics.append(mnemonic)
                    except Exception as e:
                        logger.error(f"Ошибка генерации мнемоники: {e}")
                
                # Обрабатываем каждую мнемоническую фразу
                for mnemonic in mnemonics:
                    try:
                        # Быстрая оценка приоритета
                        priority = self._calculate_priority(mnemonic)
                        
                        # Добавляем в очередь
                        if not self.output_queue.put(priority, mnemonic):
                            logger.warning("Очередь переполнена, замедляем генерацию")
                            time.sleep(0.1)
                            break
                        
                        self.generated_count += 1
                        
                    except Exception as e:
                        logger.error(f"Ошибка обработки мнемоники: {e}")
                
                # Динамическая регулировка скорости
                if self.output_queue.qsize() > config.QUEUE_SIZE * 0.8:
                    time.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"Ошибка в воркере генерации {self.worker_id}: {e}")
                time.sleep(1)
    
    def _calculate_priority(self, mnemonic: str) -> float:
        """Быстрая оценка приоритета на основе эвристик"""
        # Простые эвристики для первоначальной оценки
        words = mnemonic.split()
        unique_words = len(set(words))
        word_lengths = [len(word) for word in words]
        avg_length = sum(word_lengths) / len(word_lengths)
        
        # Базовый приоритет
        priority = 1.0
        
        # Увеличиваем приоритет для уникальных слов
        if unique_words == len(words):
            priority *= 1.5
        
        # Увеличиваем приоритет для более длинных слов
        if avg_length > 6:
            priority *= 1.2
        
        return priority

class AddressDerivationWorker:
    """Воркер для преобразования мнемонических фраз в адреса"""
    
    def __init__(self, worker_id: int, input_queue: OptimizedPriorityQueue, output_queue: OptimizedPriorityQueue):
        self.worker_id = worker_id
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.is_running = False
        self.thread = None
        self.process_pool = ProcessPoolExecutor(max_workers=config.PROCESS_POOL_WORKERS)
    
    def start(self):
        """Запуск воркера"""
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True, name=f"AddrDeriv-{self.worker_id}")
        self.thread.start()
    
    def stop(self):
        """Остановка воркера"""
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        self.process_pool.shutdown(wait=False)
    
    def _run(self):
        """Основной цикл работы воркера"""
        while self.is_running:
            try:
                # Получаем мнемоническую фразу из очереди
                priority, mnemonic = self.input_queue.get(timeout=1.0)
                
                # Пропускаем уже проверенные мнемоники
                if is_mnemonic_checked(mnemonic):
                    continue
                
                # Используем ProcessPool для CPU-bound задачи
                future = self.process_pool.submit(self._process_mnemonic, mnemonic, priority)
                
                # Обрабатываем результат (неблокирующе)
                try:
                    result_priority, task = future.result(timeout=5.0)
                    if task:
                        self.output_queue.put(result_priority, task)
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Таймаут обработки мнемоники в воркере {self.worker_id}")
                except Exception as e:
                    logger.error(f"Ошибка обработки мнемоники: {e}")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Ошибка в воркере деривации {self.worker_id}: {e}")
                time.sleep(1)
    
    def _process_mnemonic(self, mnemonic: str, initial_priority: float):
        """Обработка мнемонической фразы в отдельном процессе"""
        try:
            # Генерируем seed и адреса
            seed = mnemonic_to_seed(mnemonic)
            addresses = derive_addresses(seed)
            
            # Уточняем приоритет на основе адресов
            final_priority = self._refine_priority(initial_priority, addresses)
            
            return final_priority, WorkerTask(
                mnemonic=mnemonic,
                addresses=addresses,
                priority=final_priority
            )
        except Exception as e:
            logger.error(f"Ошибка обработки мнемоники в процессе: {e}")
            return initial_priority, None
    
    def _refine_priority(self, initial_priority: float, addresses: Dict[str, str]) -> float:
        """Уточнение приоритета на основе сгенерированных адресов"""
        priority = initial_priority
        
        # Эвристики на основе адресов
        for currency, address in addresses.items():
            if address:
                # Увеличиваем приоритет для адресов с паттернами
                if self._has_interesting_pattern(address):
                    priority *= 1.3
        
        return priority
    
    def _has_interesting_pattern(self, address: str) -> bool:
        """Проверка адреса на интересные паттерны"""
        # Быстрые проверки без сложных вычислений
        patterns = ['111', '222', '333', '444', '555', '666', '777', '888', '999', '000']
        return any(pattern in address for pattern in patterns)

class BalanceCheckWorker:
    """Асинхронный воркер для проверки балансов"""
    
    def __init__(self, worker_id: int, input_queue: OptimizedPriorityQueue, result_queue: queue.Queue):
        self.worker_id = worker_id
        self.input_queue = input_queue
        self.result_queue = result_queue
        self.is_running = False
        self.thread = None
        self.loop = None
    
    def start(self):
        """Запуск воркера"""
        self.is_running = True
        self.thread = threading.Thread(target=self._run_async, daemon=True, name=f"BalCheck-{self.worker_id}")
        self.thread.start()
    
    def stop(self):
        """Остановка воркера"""
        self.is_running = False
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
    
    def _run_async(self):
        """Запуск асинхронного цикла"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._async_run())
        finally:
            self.loop.close()
    
    async def _async_run(self):
        """Асинхронный основной цикл работы воркера"""
        from api_client import OptimizedAPIClient
        
        async with OptimizedAPIClient() as client:
            while self.is_running:
                try:
                    # Получаем задание из очереди
                    priority, task = self.input_queue.get(timeout=1.0)
                    
                    # Пропускаем уже проверенные мнемоники
                    if is_mnemonic_checked(task.mnemonic):
                        continue
                    
                    # Проверяем балансы
                    start_time = time.time()
                    balances = await client.check_balances(task.addresses)
                    processing_time = time.time() - start_time
                    
                    # Отправляем результат
                    self.result_queue.put({
                        'mnemonic': task.mnemonic,
                        'addresses': task.addresses,
                        'balances': balances,
                        'processing_time': processing_time
                    })
                    
                    # Помечаем мнемоническую фразу как проверенную
                    add_checked_mnemonic(task.mnemonic)
                    
                except queue.Empty:
                    await asyncio.sleep(0.01)
                except Exception as e:
                    logger.error(f"Ошибка в воркере проверки {self.worker_id}: {e}")
                    await asyncio.sleep(1)

class OptimizedWorkerManager:
    """Оптимизированный менеджер воркеров с улучшенной балансировкой"""
    
    def __init__(self, results_manager):
        self.results_manager = results_manager
        
        # Очереди
        self.mnemonic_queue = OptimizedPriorityQueue(maxsize=config.QUEUE_SIZE)
        self.task_queue = OptimizedPriorityQueue(maxsize=config.QUEUE_SIZE)
        self.result_queue = queue.Queue(maxsize=config.QUEUE_SIZE)
        
        # Воркеры
        self.mnemonic_workers: List[MnemonicGeneratorWorker] = []
        self.derivation_workers: List[AddressDerivationWorker] = []
        self.balance_workers: List[BalanceCheckWorker] = []
        
        # Мониторинг
        self.health_monitor = WorkerHealthMonitor()
        self.is_running = False
        
        # Статистика
        self.stats = {
            'generated': 0, 'derived': 0, 'checked': 0, 'found': 0,
            'start_time': 0, 'queue_sizes': {}
        }
    
    def start(self):
        """Запуск всех воркеров"""
        if self.is_running:
            return
        
        self.is_running = True
        self.stats['start_time'] = time.time()
        
        # Создаем воркеры генерации мнемонических фраз
        for i in range(config.PRIMARY_WORKERS):
            worker = MnemonicGeneratorWorker(i, self.mnemonic_queue)
            worker.start()
            self.mnemonic_workers.append(worker)
        
        # Создаем воркеры деривации адресов
        for i in range(config.PRIMARY_WORKERS * 2):  # Больше воркеров для CPU-bound задач
            worker = AddressDerivationWorker(i, self.mnemonic_queue, self.task_queue)
            worker.start()
            self.derivation_workers.append(worker)
        
        # Создаем воркеры проверки балансов
        for i in range(config.CHILD_WORKERS):
            worker = BalanceCheckWorker(i, self.task_queue, self.result_queue)
            worker.start()
            self.balance_workers.append(worker)
        
        # Запускаем обработчик результатов
        self.result_thread = threading.Thread(target=self._handle_results, daemon=True)
        self.result_thread.start()
        
        # Запускаем мониторинг
        self.monitor_thread = threading.Thread(target=self._monitor_workers, daemon=True)
        self.monitor_thread.start()
        
        logger.info(f"Запущено {len(self.mnemonic_workers)} генераторов, "
                   f"{len(self.derivation_workers)} дериваторов, "
                   f"{len(self.balance_workers)} проверяющих")
    
    def stop(self):
        """Остановка всех воркеров"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Останавливаем воркеры
        for worker in self.mnemonic_workers:
            worker.stop()
        for worker in self.derivation_workers:
            worker.stop()
        for worker in self.balance_workers:
            worker.stop()
        
        # Останавливаем вспомогательные потоки
        if self.result_thread.is_alive():
            self.result_thread.join(timeout=5.0)
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        logger.info("Все воркеры остановлены")
    
    def _handle_results(self):
        """Обработка результатов проверки"""
        while self.is_running:
            try:
                result = self.result_queue.get(timeout=1.0)
                self.stats['checked'] += 1
                
                # Проверяем балансы
                total_balance = 0
                for currency, balance in result['balances'].items():
                    rate = config.EXCHANGE_RATES.get(currency, 0)
                    total_balance += balance * rate
                
                # Сохраняем результат
                if total_balance >= config.MIN_TOTAL_BALANCE_USD:
                    self.stats['found'] += 1
                    self.results_manager.save_wallet_with_balance(
                        result['mnemonic'],
                        result['addresses'],
                        result['balances'],
                        total_balance
                    )
                else:
                    self.results_manager.save_empty_wallet(
                        result['mnemonic'],
                        result['addresses']
                    )
                
                # Записываем метрики производительности
                self.health_monitor.record_metrics(
                    worker_id=0,  # Анонимные метрики для результата
                    worker_type="result",
                    success=total_balance > 0,
                    processing_time=result.get('processing_time', 0)
                )
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Ошибка обработки результатов: {e}")
    
    def _monitor_workers(self):
        """Мониторинг состояния воркеров"""
        while self.is_running:
            time.sleep(5)  # Проверяем каждые 5 секунд
            
            try:
                # Обновляем статистику очередей
                self.stats['queue_sizes'] = {
                    'mnemonic': self.mnemonic_queue.qsize(),
                    'task': self.task_queue.qsize(),
                    'result': self.result_queue.qsize()
                }
                
                # Логируем статистику
                elapsed = time.time() - self.stats['start_time']
                if elapsed > 0:
                    speed = self.stats['checked'] / elapsed
                    logger.info(
                        f"Проверено: {self.stats['checked']}, "
                        f"Найдено: {self.stats['found']}, "
                        f"Скорость: {speed:.1f} кош/сек, "
                        f"Очереди: {self.stats['queue_sizes']}"
                    )
                
                # Проверяем здоровье воркеров
                healthy_count = len(self.health_monitor.healthy_workers)
                total_count = len(self.mnemonic_workers) + len(self.derivation_workers) + len(self.balance_workers)
                
                if healthy_count < total_count * 0.8:  # Меньше 80% здоровых воркеров
                    logger.warning(f"Только {healthy_count}/{total_count} воркеров здоровы")
                    
            except Exception as e:
                logger.error(f"Ошибка мониторинга: {e}")
    
    def get_stats(self) -> Dict:
        """Получение текущей статистики"""
        return self.stats.copy()