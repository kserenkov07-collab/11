# dependencies.py
# ПРОВЕРКА И УПРАВЛЕНИЕ ЗАВИСИМОСТЯМИ
# Автор: Колин для выживания деревни

import importlib
import sys

class DependencyManager:
    def __init__(self):
        self.available_deps = {}
        self.check_dependencies()
        
    def check_dependencies(self):
        """Проверка доступности всех зависимостей"""
        dependencies = {
            'pandas': 'pandas',
            'numpy': 'numpy',
            'scipy': 'scipy',
            'sympy': 'sympy',
            'matplotlib': 'matplotlib',
            'tinkoff': 'tinkoff.invest',
            'aiohttp': 'aiohttp',
            'sklearn': 'sklearn',
            'selenium': 'selenium',
            'opcua': 'opcua',
            'pymodbus': 'pymodbus',
            'sqlalchemy': 'sqlalchemy',
            'bs4': 'bs4',
            'requests': 'requests',
            'textblob': 'textblob'
        }
        
        for name, module in dependencies.items():
            try:
                importlib.import_module(module)
                self.available_deps[name] = True
                print(f"✓ {name} доступен")
            except ImportError:
                self.available_deps[name] = False
                print(f"✗ {name} недоступен")
                
    def is_available(self, dep_name):
        """Проверка доступности конкретной зависимости"""
        return self.available_deps.get(dep_name, False)
        
    def get_missing_deps(self):
        """Получение списка отсутствующих зависимостей"""
        return [name for name, available in self.available_deps.items() if not available]
