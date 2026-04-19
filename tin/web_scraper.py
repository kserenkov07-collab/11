# web_scraper.py
# МОДУЛЬ ДЛЯ ВЕБ-СКРАПИНГА С ОПЦИОНАЛЬНЫМИ ЗАВИСИМОСТЯМИ
# Автор: Колин для выживания деревни

from dependencies import DependencyManager
from datetime import datetime
import json

# Проверяем доступность зависимостей
deps = DependencyManager()

# Пытаемся импортировать опциональные зависимости
if deps.is_available('selenium'):
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        SELENIUM_AVAILABLE = True
    except:
        SELENIUM_AVAILABLE = False
else:
    SELENIUM_AVAILABLE = False

if deps.is_available('bs4'):
    try:
        from bs4 import BeautifulSoup
        BS4_AVAILABLE = True
    except:
        BS4_AVAILABLE = False
else:
    BS4_AVAILABLE = False

if deps.is_available('requests'):
    try:
        import requests
        REQUESTS_AVAILABLE = True
    except:
        REQUESTS_AVAILABLE = False
else:
    REQUESTS_AVAILABLE = False

class WebDataScraper:
    def __init__(self):
        self.driver = None
        self.wait = None
        
        print(f"Selenium доступен: {SELENIUM_AVAILABLE}")
        print(f"BeautifulSoup доступен: {BS4_AVAILABLE}")
        print(f"Requests доступен: {REQUESTS_AVAILABLE}")
        
        if SELENIUM_AVAILABLE:
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")  # Фоновый режим
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, 10)
            except Exception as e:
                print(f"Ошибка инициализации Selenium: {e}")
                SELENIUM_AVAILABLE = False
        
    def scrape_financial_news(self):
        """Сбор финансовых новостей"""
        news_data = []
        
        # Если Selenium недоступен, возвращаем тестовые данные
        if not SELENIUM_AVAILABLE:
            # Тестовые данные для демонстрации
            return [
                {
                    'title': 'Тестовая новость 1: Рынок акций показывает рост',
                    'link': 'https://example.com/news1',
                    'source': 'simulated',
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'title': 'Тестовая новость 2: Центробанк оставил ставку без изменений',
                    'link': 'https://example.com/news2',
                    'source': 'simulated',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        
        try:
            # Пример: сбор новостей с Reuters
            self.driver.get("https://www.reuters.com/business/finance/")
            
            # Ожидание загрузки новостей
            news_elements = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='Heading']"))
            )
            
            for element in news_elements[:10]:  # Первые 10 новостей
                try:
                    title = element.text
                    link = element.find_element(By.XPATH, "./..").get_attribute("href")
                    news_data.append({
                        'title': title,
                        'link': link,
                        'source': 'reuters',
                        'timestamp': datetime.now().isoformat()
                    })
                except:
                    continue
                    
        except Exception as e:
            print(f"Ошибка сбора новостей: {e}")
            
        return news_data
        
    def scrape_economic_indicators(self):
        """Сбор экономических индикаторов"""
        economic_data = {}
        
        # Если зависимости недоступны, возвращаем тестовые данные
        if not REQUESTS_AVAILABLE or not BS4_AVAILABLE:
            # Тестовые данные для демонстрации
            return {
                'USA': {
                    'rate': '5.5%',
                    'change': '+0.25%',
                    'timestamp': datetime.now().isoformat()
                },
                'EU': {
                    'rate': '4.0%',
                    'change': '0.0%',
                    'timestamp': datetime.now().isoformat()
                }
            }
        
        try:
            # Пример: получение данных о ключевых ставках
            url = "https://www.investing.com/central-banks/"
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Поиск таблицы с ставками
            table = soup.find('table', {'id': 'cr_1'})
            if table:
                rows = table.find_all('tr')[1:]  # Пропуск заголовка
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        country = cols[0].text.strip()
                        rate = cols[1].text.strip()
                        change = cols[3].text.strip()
                        
                        economic_data[country] = {
                            'rate': rate,
                            'change': change,
                            'timestamp': datetime.now().isoformat()
                        }
                        
        except Exception as e:
            print(f"Ошибка сбора экономических индикаторов: {e}")
            
        return economic_data
        
    def scrape_stock_sentiment(self, tickers):
        """Сбор данных о настроениях по акциям"""
        sentiment_data = {}
        
        # Если Selenium недоступен, возвращаем тестовые данные
        if not SELENIUM_AVAILABLE:
            # Тестовые данные для демонстрации
            for ticker in tickers:
                sentiment_data[ticker] = {
                    'price': 100.0,
                    'change': 1.5,
                    'sentiment': 'bullish',
                    'timestamp': datetime.now().isoformat()
                }
            return sentiment_data
        
        for ticker in tickers:
            try:
                # Пример: анализ настроений с Yahoo Finance
                url = f"https://finance.yahoo.com/quote/{ticker}"
                self.driver.get(url)
                
                # Получение цены и изменения
                price_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-field="regularMarketPrice"]'))
                )
                change_element = self.driver.find_element(By.CSS_SELECTOR, '[data-field="regularMarketChangePercent"]')
                
                price = float(price_element.text)
                change = float(change_element.text.strip('%'))
                
                # Определение настроения на основе изменения цены
                sentiment = "bullish" if change > 0 else "bearish" if change < 0 else "neutral"
                
                sentiment_data[ticker] = {
                    'price': price,
                    'change': change,
                    'sentiment': sentiment,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"Ошибка сбора настроений для {ticker}: {e}")
                continue
                
        return sentiment_data
        
    def analyze_news_sentiment(self, news_data):
        """Анализ тональности новостей"""
        # Упрощенный анализ тональности без textblob
        positive_words = ['рост', 'увеличение', 'прибыль', 'успех', 'позитивный']
        negative_words = ['падение', 'снижение', 'убыток', 'проблема', 'негативный']
        
        sentiment_scores = []
        
        for news in news_data:
            try:
                # Простой анализ на основе ключевых слов
                title = news['title'].lower()
                positive_count = sum(1 for word in positive_words if word in title)
                negative_count = sum(1 for word in negative_words if word in title)
                
                score = (positive_count - negative_count) / max(1, len(title.split()))
                sentiment_scores.append(score)
            except:
                continue
                
        # Расчет среднего показателя тональности
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            overall_sentiment = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"
        else:
            avg_sentiment = 0
            overall_sentiment = "neutral"
            
        return {
            'average_sentiment': avg_sentiment,
            'overall_sentiment': overall_sentiment,
            'timestamp': datetime.now().isoformat()
        }
        
    def close(self):
        """Закрытие веб-драйвера"""
        if self.driver and SELENIUM_AVAILABLE:
            self.driver.quit()
