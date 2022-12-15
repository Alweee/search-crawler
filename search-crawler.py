import os

from pathlib import Path

import sqlite3

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import pandas as pd

import telebot
from telebot import types

load_dotenv()

MIME_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

bot = telebot.TeleBot(os.getenv('BOT_TOKEN'))


@bot.message_handler(commands=['start', 'help'])
def start(message):
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
    try:
        file_name = message.document.file_name
        file_obj = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_obj.file_path)

        file_path = Path(Path(). absolute(), 'user_files',
                         f'user_{message.chat.first_name}', file_name)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
    except Exception as error:
        raise (f'Сбой при сохранении файла: {error}')
    else:
        handle_file(message, file_path)


def handle_file(message, path):
    """
    Открывает файл библиотекой pandas и выводит
    содержимое файла сообщением пользователю.
    """
    try:
        df = pd.read_excel(path)

        text = 'Содержимое файла:'
        for i in range(len(df)):
            text += ('\n\n name: ' + str((df['name'].iloc[i])) + '\n '
                     'url: ' + str((df['url'].iloc[i])) + '\n '
                     'xpath: ' + str((df['xpath'].iloc[i])))
    except Exception as error:
        raise (f'Сбой при работе с файлом: {error}')
    else:
        bot.send_message(message.chat.id, text)
        save_file_content_to_database(message, df)


def save_file_content_to_database(message, df):
    """
    Сохраняет содержимое файла в локальную базу данных sqlite.
    """
    try:
        conn = sqlite3.connect('parsing_data.db')
        c = conn.cursor()
        # c.execute('''CREATE TABLE zuzubliks(name TEXT,url TEXT, xpath TEXT)''')

        content = []
        for i in range(len(df)):
            content.append((df['name'].iloc[i],
                            df['url'].iloc[i],
                            df['xpath'].iloc[i]))

        c.executemany('''INSERT INTO zuzubliks VALUES(?,?,?)''', content)
        conn.commit()
        conn.close()
    except Exception as error:
        raise (f'Сбой при сохранении данных в базу: {error}')
    else:
        scraping_by_file_content(message, content)


def scraping_by_file_content(message, content):
    """
    Проводит парсинг по данным из таблицы и выводит сообщение
    пользователю со средней ценой сущности на одной странице.
    """
    avg_price_message = ''

    for i in range(len(content)):
        url = content[i][1]

        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.get(url)

        xpath_query = content[i][2]

        product_cards = driver.find_elements(By.XPATH, xpath_query)

        sum = 0
        for card in product_cards:
            price = int(card.text.replace(' ', '').replace('₽', ''))
            sum += price

        avg_price = (sum)//len(product_cards)

        avg_price_message += (f'Средняя цена товара '
                              f'"{content[i][0]}" = {avg_price}.\n')

    bot.send_message(message.chat.id, avg_price_message)


bot.infinity_polling()
