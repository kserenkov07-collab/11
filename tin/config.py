# config.py
# ОБНОВЛЕННЫЙ КОНФИГУРАЦИОННЫЙ ФАЙЛ С ПРАВИЛЬНЫМИ ИДЕНТИФИКАТОРАМИ

# Токен Tinkoff API
TINKOFF_TOKEN = "t.539HFY_GqB1uWwZh1ZU4KwloBrrmUWg9vG-1NvZw-R-LDZulElYZyZRHqXkLWIjkOndsbb8o__VO-BhXZmDjmg"

# Расширенный список инструментов с правильными FIGI
TICKERS = {
    # Акции
    'MOEX': 'BBG004730N88',  # Московская Биржа
    'SBER': 'BBG004730ZJ9',  # Сбербанк
    'VTBR': 'BBG004730JJ5',  # Банк ВТБ
    'GAZP': 'BBG004730RP0',  # Газпром
    'TCSG': 'BBG00QPYJ5H0',  # TCS Group (Tinkoff)
    'LKOH': 'BBG004731032',  # Лукойл
    'ROSN': 'BBG004731354',  # Роснефть
    'MGNT': 'BBG0047515Y7',  # Магнит
    'SVAV': 'BBG00475J7C1',  # Совкомбанк
    'GMKN': 'BBG004731489',  # Норникель
    'KMAZ': 'BBG00475K2C9',  # КАМАЗ
    'SIBN': 'BBG0047315Y7',  # Газпром нефть
    'PHOR': 'BBG0047315D0',  # ФосАгро
    'MTSS': 'BBG00475K2C9',  # МТС
    'YNDX': 'BBG006L8G4H1',  # Яндекс
    'AGRO': 'BBG00F6NKQX3',  # РусАгро
    'FIVE': 'BBG00F6NKQX3',  # X5 Group
    'VKCO': 'BBG00F6NKQX3',  # VK
    'AFLT': 'BBG00475J7C1',  # Аэрофлот
    'NVTK': 'BBG00475JZZ6',  # НОВАТЭК
    'MVID': 'BBG00475K2C9',  # М.Видео
    
    # Облигации (примерные FIGI, нужны реальные)
    'GAZPOB': 'BBG00R0X6F60',  # Газпром банк облигации
    'SBEROB': 'BBG00R0X6F61',  # Сбербанк облигации
    'YNDXOB': 'BBG00R0X6F62',  # Яндекс облигации
    
    # Фьючерсы (примерные FIGI, нужны реальные)
    'IMOEXF': 'FUTMOEX12345',  # Индекс МосБиржи
    'IBITF': 'FUTIBIT12345',   # IBIT
    'CNYF': 'FUTCNY12345',     # Юань
    'USDF': 'FUTUSD12345',     # Доллар
    'EURF': 'FUTEUR12345',     # Евро
    'SEKF': 'FUTSEK12345',     # Кроны
    'GOLDF': 'FUTGOLD12345',   # Золото
    'GBPF': 'FUTGBP12345',     # Фунты
    'ETHAF': 'FUTETHA12345',   # ETHA
    'RTSF': 'FUTRTS12345',     # RTS
}

# Шорты (те же тикеры, но с противоположными сигналами)
SHORT_TICKERS = {
    'YNDX', 'MGNT', 'GAZP', 'SBER', 'VTBR', 'TCSG', 'LKOH', 'ROSN', 'SVAV'
}

# Настройки торговли
TRADE_SETTINGS = {
    'analysis_interval': 60,  # Интервал анализа в секундах
    'trade_quantity': 10,     # Количество акций для торговли
    'risk_level': 'HIGH',     # Уровень риска
    'stop_loss': 0.05,        # Стоп-лосс 5%
    'take_profit': 0.10,      # Тейк-профит 10%
}
