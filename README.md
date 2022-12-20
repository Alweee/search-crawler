# search-crawler
Simple-Web-search-bot

### Шаблон наполнения `.env` файла:
- BOT_TOKEN=5914070477:AAEMKdUub3nfJOKdozLrTY1gO7rcyl4ay8o

### Запустить бота в докер контейнере:

- `docker build -t search-crawler .`

- `docker run --name search-crawler search-crawler`

### Протестировать https://t.me/SearchCrawlerBot.
- Бот задеплоен на удалённом сервере, в докер контейнере.

- Тестовый файл для проверки работоспособности бота находится в директории `test_data/`



### В планах по улучшению:
- Проводить парсинг по нескольким страницам и более гибко, а не только по одной.
- Добавить docker-compose.
- Улучшить взаимодействие с пользователем.


