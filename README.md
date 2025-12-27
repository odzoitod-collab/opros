# 🎄 Новорічний Опитувальник

Telegram бот для збору побажань друзів на Новий Рік.

## Налаштування

1. Відкрий `opros.py` і заміни:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Токен від @BotFather
ADMIN_ID = 123456789  # Твій Telegram ID (дізнатись: @userinfobot)
```

## Локальний запуск

```bash
pip install -r requirements.txt
python opros.py
```

## Хостинг

### Railway.app (рекомендую)
1. Зареєструйся на https://railway.app
2. New Project → Deploy from GitHub repo
3. Бот запуститься автоматично

### Heroku
1. Створи app на heroku.com
2. Підключи GitHub репо
3. Deploy

### VPS (Ubuntu)
```bash
# Встанови Python
sudo apt update
sudo apt install python3 python3-pip

# Клонуй репо
git clone <твій-репо>
cd <папка>

# Встанови залежності
pip3 install -r requirements.txt

# Запусти в фоні
nohup python3 opros.py &
```

### Systemd сервіс (VPS)
```bash
sudo nano /etc/systemd/system/nybot.service
```

Вставити:
```ini
[Unit]
Description=New Year Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/bot
ExecStart=/usr/bin/python3 /root/bot/opros.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Запустити:
```bash
sudo systemctl enable nybot
sudo systemctl start nybot
```

## Команди бота

- `/start` — почати опитування
- `/reset` — скинути і почати заново
- `/delete_my_data` — видалити свої відповіді

Адмін бачить кнопку 📊 Статистика
