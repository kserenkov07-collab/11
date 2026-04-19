# industrial_integration.py
# МОДУЛЬ ДЛЯ ИНТЕГРАЦИИ С ПРОМЫШЛЕННЫМИ СИСТЕМАМИ (ОПЦИОНАЛЬНЫЕ ЗАВИСИМОСТИ)
# Автор: Колин для выживания деревни

from dependencies import DependencyManager
from datetime import datetime
import json

# Проверяем доступность зависимостей
deps = DependencyManager()

# Пытаемся импортировать опциональные зависимости
if deps.is_available('opcua'):
    try:
        from opcua import Client, ua
        OPCUA_AVAILABLE = True
    except:
        OPCUA_AVAILABLE = False
else:
    OPCUA_AVAILABLE = False

if deps.is_available('pymodbus'):
    try:
        from pymodbus.client import ModbusTcpClient
        from pymodbus.exceptions import ModbusException
        MODBUS_AVAILABLE = True
    except:
        MODBUS_AVAILABLE = False
else:
    MODBUS_AVAILABLE = False

class IndustrialDataMonitor:
    def __init__(self):
        self.opcua_client = None
        self.modbus_client = None
        self.industrial_data = {}
        self.connection_status = {
            'opcua': False,
            'modbus': False
        }
        
        print(f"OPCUA доступен: {OPCUA_AVAILABLE}")
        print(f"Modbus доступен: {MODBUS_AVAILABLE}")
        
    async def connect_opcua(self, server_url):
        """Подключение к OPC UA серверу"""
        if not OPCUA_AVAILABLE:
            print("OPCUA недоступен. Установите библиотеку opcua для использования этой функции.")
            return False
            
        try:
            self.opcua_client = Client(server_url)
            # Для асинхронного подключения может потребоваться дополнительная настройка
            self.opcua_client.connect()
            self.connection_status['opcua'] = True
            print(f"Подключение к OPC UA серверу {server_url} установлено")
            return True
        except Exception as e:
            print(f"Ошибка подключения к OPC UA: {e}")
            return False
            
    def connect_modbus(self, host, port=502):
        """Подключение к Modbus устройству"""
        if not MODBUS_AVAILABLE:
            print("Modbus недоступен. Установите библиотеку pymodbus для использования этой функции.")
            return False
            
        try:
            self.modbus_client = ModbusTcpClient(host, port)
            self.connection_status['modbus'] = self.modbus_client.connect()
            if self.connection_status['modbus']:
                print(f"Подключение к Modbus устройству {host}:{port} установлено")
            return self.connection_status['modbus']
        except Exception as e:
            print(f"Ошибка подключения к Modbus: {e}")
            return False
            
    def read_opcua_data(self, node_ids):
        """Чтение данных из OPC UA сервера"""
        data = {}
        if not self.connection_status['opcua'] or not OPCUA_AVAILABLE:
            return data
            
        try:
            for name, node_id in node_ids.items():
                node = self.opcua_client.get_node(node_id)
                value = node.get_value()
                data[name] = {
                    'value': value,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'opcua'
                }
        except Exception as e:
            print(f"Ошибка чтения данных OPC UA: {e}")
            
        return data
        
    def read_modbus_data(self, address_map):
        """Чтение данных из Modbus устройства"""
        data = {}
        if not self.connection_status['modbus'] or not MODBUS_AVAILABLE:
            return data
            
        try:
            for name, config in address_map.items():
                address = config['address']
                register_type = config['type']
                count = config.get('count', 1)
                
                if register_type == 'coil':
                    result = self.modbus_client.read_coils(address, count)
                    value = result.bits[0] if result else None
                elif register_type == 'input':
                    result = self.modbus_client.read_discrete_inputs(address, count)
                    value = result.bits[0] if result else None
                elif register_type == 'holding':
                    result = self.modbus_client.read_holding_registers(address, count)
                    value = result.registers[0] if result else None
                elif register_type == 'input_register':
                    result = self.modbus_client.read_input_registers(address, count)
                    value = result.registers[0] if result else None
                else:
                    value = None
                    
                if value is not None:
                    # Применение scaling factor если указан
                    scale = config.get('scale', 1)
                    data[name] = {
                        'value': value * scale,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'modbus'
                    }
                    
        except Exception as e:
            print(f"Ошибка чтения данных Modbus: {e}")
            
        return data
        
    def monitor_industrial_data(self):
        """Мониторинг промышленных данных"""
        # Если зависимости недоступны, возвращаем тестовые данные
        if not OPCUA_AVAILABLE and not MODBUS_AVAILABLE:
            # Генерация тестовых данных для демонстрации
            import random
            self.industrial_data = {
                'temperature': {
                    'value': random.uniform(20, 30),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'simulated'
                },
                'pressure': {
                    'value': random.uniform(100, 200),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'simulated'
                },
                'production_rate': {
                    'value': random.uniform(50, 100),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'simulated'
                }
            }
            return self.industrial_data
        
        # Конфигурация OPC UA узлов (пример)
        opcua_nodes = {
            'temperature': 'ns=2;i=1',
            'pressure': 'ns=2;i=2',
            'flow_rate': 'ns=2;i=3',
            'energy_consumption': 'ns=2;i=4'
        }
        
        # Конфигурация Modbus устройств (пример)
        modbus_map = {
            'production_rate': {'address': 0, 'type': 'holding', 'scale': 0.1},
            'equipment_status': {'address': 1, 'type': 'coil'},
            'quality_metric': {'address': 2, 'type': 'input_register', 'scale': 0.01}
        }
        
        # Чтение данных
        opcua_data = self.read_opcua_data(opcua_nodes)
        modbus_data = self.read_modbus_data(modbus_map)
        
        # Объединение данных
        self.industrial_data = {**opcua_data, **modbus_data}
        
        return self.industrial_data
        
    def get_industrial_correlations(self, market_data):
        """Анализ корреляций между промышленными и рыночными данными"""
        correlations = {}
        
        # Для упрощения возвращаем тестовые корреляции
        # В реальной системе здесь был бы сложный анализ
        for ind_key in self.industrial_data.keys():
            for market_key in market_data.keys():
                # Простая "фейковая" корреляция для демонстрации
                correlations[f"{ind_key}_{market_key}"] = 0.5
        
        return correlations
        
    def disconnect(self):
        """Отключение от промышленных систем"""
        if self.opcua_client and OPCUA_AVAILABLE:
            self.opcua_client.disconnect()
        if self.modbus_client and MODBUS_AVAILABLE:
            self.modbus_client.close()
            
        self.connection_status = {
            'opcua': False,
            'modbus': False
        }
        print("Отключение от промышленных систем завершено")
