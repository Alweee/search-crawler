import os

from pathlib import Path

import sqlite3

from dotenv import load_dotenv

from selenium.webdriver.chrome.options import Options
from selenium import webdriver

import pandas as pd

import telebot
from telebot import types

load_dotenv()

MIME_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))


def set_chrome_options():
    """Устанавливает параметры chrome для Selenium.
       Параметры Chrome для безголового браузера включены.
    """
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_prefs = {}
    chrome_options.experimental_options['prefs'] = chrome_prefs
    chrome_prefs['profile.default_content_settings'] = {'images': 2}
    return chrome_options


@bot.message_handler(commands=['start', 'help'])
def start(message):
    """Начало работы бота."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton(text='Загрузить файл')
    markup.add(button1)

    bot.send_message(
        message.chat.id,
        f'{message.chat.first_name}, привет!\nЯ бот, сборщик информации.',
        reply_markup=markup)


@bot.message_handler(func=lambda button: button.text == 'Загрузить файл')
def handle_button(message):
    bot.send_message(message.chat.id, 'OK.Пришли мне свой excel файл.')


def test_file_type(message):
    return message.document.mime_type == MIME_TYPE


@bot.message_handler(func=test_file_type, content_types=['document'])
def save_file(message):
    """Получает файл от пользователя и сохранет его."""
    file_name = message.document.file_name
    file_obj = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_obj.file_path)

    file_path = Path(Path(). absolute(), 'user_files',
                     f'user_{message.chat.first_name}', file_name)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'wb') as f:
        f.write(downloaded_file)

    handle_file(message, file_path)


def handle_file(message, path):
    """
    Открывает файл библиотекой pandas и выводит
    содержимое файла сообщением пользователю.
    """
    df = pd.read_excel(path)

    text = 'Содержимое файла:'

    for i in range(len(df)):
        text += ('\n\n name: ' + str((df['name'].iloc[i])) + '\n '
                 'url: ' + str((df['url'].iloc[i])) + '\n '
                 'xpath: ' + str((df['xpath'].iloc[i])))

    bot.send_message(message.chat.id, text)

    save_file_content_to_database(message, df)


def save_file_content_to_database(message, df):
    """
    Сохраняет содержимое файла в локальную базу данных sqlite.
    """
    try:
        conn = sqlite3.connect('parsing_data.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE zuzubliks(name TEXT,url TEXT, xpath TEXT)''')

    except sqlite3.OperationalError:
        pass

    finally:
        content = []
        for i in range(len(df)):
            content.append((df['name'].iloc[i],
                            df['url'].iloc[i],
                            df['xpath'].iloc[i]))

        c.executemany('''INSERT INTO zuzubliks VALUES(?,?,?)''', content)
        conn.commit()
        conn.close()

    scraping_by_file_content(message, content)


def scraping_by_file_content(message, content):
    """
    Проводит парсинг по данным из таблицы и выводит сообщение
    пользователю со средней ценой сущности на одной странице.
    """
    chrome_options = set_chrome_options()

    driver = webdriver.Chrome(options=chrome_options)

    avg_price_message = ''

    for i in range(len(content)):
        url = content[i][1]

        driver.get(url)

        xpath_query = content[i][2]

        product_cards = driver.find_elements('xpath', xpath_query)

        sum = 0
        for card in product_cards:
            price = int(card.text.replace(' ', '').replace('₽', ''))
            sum += price

        try:
            avg_price = (sum)//len(product_cards)
        except ZeroDivisionError:
            avg_price = 'Нас раскрыли:) попробуйте позже'

        avg_price_message += (f'Средняя цена товара '
                              f'"{content[i][0]}" -> {avg_price}\n')

    bot.send_message(message.chat.id, avg_price_message)

    driver.close()


bot.infinity_polling()
