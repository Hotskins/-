import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import concurrent.futures

# Настройки API
API_KEY = "ba08c89569134e42aa25de2ed11d8463"  # Ваш API-ключ
SERVICE = "ya"  # Код для Yandex
COUNTRY = "ru"  # Код страны
BASE_URL = "https://vak-sms.com/api"
OUTPUT_FILE = "accounts.txt"  # Файл для сохранения данных аккаунтов

def get_number(operator="vector"):
    """Получить временный номер для сервиса с фильтрацией по оператору."""
    url = f"{BASE_URL}/getNumber/"
    params = {
        "apiKey": API_KEY,
        "service": SERVICE,
        "country": COUNTRY,
        "operator": operator
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "tel" in data and "idNum" in data:
            print(f"Получен номер: {data['tel']} от оператора {operator}")
            return data["tel"], data["idNum"]
        else:
            print(f"Ошибка получения номера: {data.get('error', 'Unknown error')}")
            return None, None
    except requests.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None, None

def get_sms_code(id_num):
    """Ожидать получения кода подтверждения."""
    url = f"{BASE_URL}/getSmsCode/"
    params = {"apiKey": API_KEY, "idNum": id_num}
    for _ in range(25):
        response = requests.get(url, params=params)
        data = response.json()
        if "smsCode" in data and data["smsCode"]:
            print(f"Получен SMS-код: {data['smsCode']}")
            return data["smsCode"]
        print("Ожидание SMS-кода...")
        time.sleep(5)
    print("Не удалось получить SMS-код.")
    return None

def wait_and_click(driver, by, value, timeout=10):
    """Ожидать и кликнуть по элементу."""
    try:
        element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
        element.click()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Ошибка при клике: {e}")
        return False

def wait_and_send_keys(driver, by, value, text, timeout=10):
    """Ожидать элемент и ввести текст."""
    try:
        element = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
        element.clear()
        element.send_keys(text)
        return True
    except Exception as e:
        print(f"Ошибка при вводе текста: {e}")
        return False

def wait_and_send_keys_with_enter(driver, by, value, text, timeout=10):
    """
    Ожидать элемент, очистить поле, ввести текст и нажать Enter.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        element.clear()  # Очищает поле перед вводом текста
        element.send_keys(text)
        element.send_keys(Keys.RETURN)
        print(f"Введено значение '{text}' и нажато Enter.")
        return True
    except Exception as e:
        print(f"Ошибка при вводе текста с Enter: {e}")
        return False


def wait_for_text_and_retry_call(driver, text_to_wait, retry_button_xpath, delay=70):
    """
    Ожидать текст и, спустя заданное время, нажать кнопку 'Звонка не было'.
    
    Args:
        driver: WebDriver instance.
        text_to_wait: Текст, который нужно обнаружить.
        retry_button_xpath: XPath кнопки для нажатия.
        delay: Время ожидания перед нажатием кнопки (в секундах).
    """
    try:
        # Ожидание появления текста
        WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text_to_wait))
        print(f"Текст '{text_to_wait}' найден. Ожидание {delay} секунд перед нажатием кнопки...")
        
        # Ждём указанное время перед нажатием кнопки
        time.sleep(delay)
        
        # Нажатие кнопки
        retry_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, retry_button_xpath)))
        retry_button.click()
        print("Нажата кнопка 'Звонка не было'.")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"Ошибка при ожидании текста или нажатии кнопки: {e}")
        return False


def get_random_name(file_path):
    """Получить случайное имя или фамилию из текстового файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            return random.choice(lines).strip() if lines else None
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")
        return None

def save_account_data(firstname, lastname, phone, login, password):
    """Сохранить данные аккаунта в файл."""
    with open(OUTPUT_FILE, "a", encoding="utf-8") as file:
        file.write(f"{firstname} {lastname} - {phone} - {login}:{password}\n")
        print(f"Данные аккаунта сохранены: {firstname} {lastname} - {phone} - {login}:{password}")

def setup_browser():
    """Настройка Selenium WebDriver."""
    options = Options()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def register_account():
    """Регистрация аккаунта на Яндексе."""
    while True:
        phone, id_num = get_number()
        if not phone or not id_num:
            return

        firstname = get_random_name("firstnames.txt")
        lastname = get_random_name("lastnames.txt")
        if not firstname or not lastname:
            print("Не удалось получить имя или фамилию. Проверьте текстовые файлы.")
            return

        driver = setup_browser()
        try:
            # Шаг 1: Перейти на страницу регистрации
            driver.get("https://360.yandex.ru/mail/")
            wait_and_click(driver, By.CSS_SELECTOR, "a[data-test='start-use-button']")

            # Шаг 2: Ввод номера телефона
            wait_and_send_keys(driver, By.ID, "passp-field-phone", phone)
            driver.find_element(By.ID, "passp-field-phone").send_keys(Keys.RETURN)

            # Обработка текста "Введите последние 6 цифр входящего номера"
            text_to_wait = "Введите последние 6 цифр входящего номера"
            retry_button_xpath = "//button[@data-t='button:default:retry-to-request-code']"
            wait_for_text_and_retry_call(driver, text_to_wait, retry_button_xpath, delay=70)


            # Шаг 3: Ввод SMS-кода
            sms_code = get_sms_code(id_num)
            if not sms_code:
                print("Не удалось получить SMS-код.")
                return

            wait_and_send_keys(driver, By.ID, "passp-field-phoneCode", sms_code)
            driver.find_element(By.ID, "passp-field-phoneCode").send_keys(Keys.RETURN)

            # Шаг 4: Ввод имени и фамилии
            wait_and_send_keys_with_enter(driver, By.ID, "passp-field-firstname", firstname)
            wait_and_send_keys_with_enter(driver, By.ID, "passp-field-lastname", lastname)

            # Шаг 5: Ввод логина
            login = f"user{random.randint(100000, 999999)}"
            wait_and_send_keys_with_enter(driver, By.ID, "passp-field-login", login)


            # Шаг 6: Установка пароля
            password = "StrongPassword123!"
            wait_and_send_keys_with_enter(driver, By.ID, "passp-field-password", password)

            # Шаг 7: Сохранение данных аккаунта
            save_account_data(firstname, lastname, phone, login, password)
            print("Регистрация успешно завершена!")
            break

        except Exception as e:
            print(f"Ошибка выполнения скрипта: {e}")
        finally:
            driver.quit()

def main():
    """Запуск регистрации аккаунтов в нескольких потоках."""
    num_threads = 2  # Количество потоков
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            futures.append(executor.submit(register_account))
            time.sleep(10)
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Ошибка в потоке: {e}")

if __name__ == "__main__":
    main()
