# Cinema Bot

![сinema-bot](https://github.com/user-attachments/assets/be280e49-d655-4326-a0f5-32e29867101d)

**Cinema Bot** - это бот для поиска информации о фильмах и сериалах.

Он использует `API OMDB` для получения данных о фильмах и сохраняет историю поисков для каждого пользователя.

## Структура проекта

```
cinema_bot/
│
├── .env                     # Файл с конфиденциальными данными (токены, API ключи, путь к базе данных)
├── .gitignore               # Файл для игнорирования конфиденциальных данных в репозитории
├── bot.py                   # Основной файл бота с логикой
├── db.py                    # Файл для работы с базой данных
├── сache.py                 # Кеширование запросов
├── requirements.txt         # Зависимости проекта
├── LICENSE                  # Лицензия проекта
└── README.md                # Документация для проекта
```

## Установка

1. **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/your-username/cinema-bot.git
    cd cinema-bot
    ```

2. **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Создайте `.env` файл и добавьте свои конфиденциальные данные:**
    ```
    BOT_TOKEN=your_bot_token_here
    OMDB_API_KEY=your_omdb_api_key_here
    DB_PATH=cinema_bot.db
    ```

4. **Запустите бота:**
    ```bash
    python bot.py
    ```

## Команды

- `/start` - Приветственное сообщение
- `/help` - Инструкция по использованию
- `/history` - История ваших поисков
- `/stats` - Статистика по количеству поисков

---

### 📄 Лицензия

[Этот проект лицензирован под лицензией MIT](LICENCE)

Для получения дополнительной информации ознакомьтесь с файлом `LICENSE`

---

### Автор

**Дуплей Максим Игоревич**

**Дата:** 09.12.2024

**Версия:** 1.0
