# 🤖 Telegram Bot Template

Production-ready boilerplate for Telegram bots built with **aiogram 3**, **SQLAlchemy 2**, and **structlog**.  
Zero business logic — just clean architecture ready for your code.

---

## ⚡ Быстрый старт (5 минут)

```bash
# 1. Клонировать и настроить
git clone https://github.com/yourname/telegram-bot-template.git
cd telegram-bot-template
cp .env.example .env
# Вставьте ваш токен в BOT_TOKEN в файле .env

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить
python -m bot.main
```

Готово. Бот работает в режиме polling.

---

## 📁 Структура проекта

```
telegram-bot-template/
├── bot/
│   ├── config.py              # Конфигурация через pydantic-settings
│   ├── main.py                # Точка входа (polling / webhook)
│   ├── database/
│   │   ├── __init__.py        # Engine, SessionFactory, create_tables()
│   │   ├── models.py          # ORM-модели: User, Session
│   │   ├── repository.py      # CRUD: UserRepository, SessionRepository
│   │   └── migrations/        # Alembic (env.py + versions/)
│   ├── handlers/
│   │   ├── __init__.py        # register_handlers(dp) — агрегатор роутеров
│   │   ├── commands.py        # /start, /help, /settings
│   │   ├── messages.py        # Обработка свободного текста
│   │   └── callbacks.py       # Inline-кнопки
│   ├── keyboards/
│   │   └── inline.py          # Фабрики клавиатур (main_menu, confirm, paginate...)
│   ├── middlewares/
│   │   ├── __init__.py        # register_middlewares(dp)
│   │   ├── logging.py         # Логирование каждого update
│   │   └── throttling.py      # Анти-спам (token per user)
│   ├── services/
│   │   └── __init__.py        # Сервисный слой (ваша бизнес-логика)
│   └── utils/
│       └── logger.py          # structlog setup (text / JSON)
├── tests/
│   ├── conftest.py            # Shared fixtures (DB, bot, mocks)
│   ├── unit/
│   │   └── test_repository.py
│   └── handlers/
│       └── test_commands.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example
├── .pre-commit-config.yaml
├── alembic.ini
├── pyproject.toml
└── requirements.txt
```

---

## ⚙️ Конфигурация

Все настройки задаются через переменные окружения или файл `.env`:

| Переменная | Описание | По умолчанию |
|---|---|---|
| `BOT_TOKEN` | **Обязательно.** Токен из @BotFather | — |
| `ENVIRONMENT` | `development` / `staging` / `production` | `development` |
| `BOT_MODE` | `polling` / `webhook` | `polling` |
| `DATABASE_URL` | SQLAlchemy async URL | SQLite (dev.db) |
| `REDIS_URL` | `redis://host:6379/0` | `None` |
| `THROTTLE_RATE` | Мин. секунд между запросами пользователя | `0.5` |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` | `INFO` |
| `LOG_JSON` | JSON-логи для production | `false` |

---

## ➕ Как добавить новую команду

**Шаг 1.** Добавьте хендлер в `bot/handlers/commands.py`:

```python
from aiogram.filters import Command

@router.message(Command("mycommand"))
async def cmd_mycommand(message: Message) -> None:
    """Описание команды."""
    await message.answer("Ваш ответ здесь")
```

**Шаг 2.** Зарегистрируйте команду в `bot/main.py` внутри `set_commands()`:

```python
BotCommand(command="mycommand", description="Описание для меню"),
```

Роутер команд уже подключён — больше ничего делать не нужно.

---

## 🔌 Как подключить бизнес-логику

**1. Создайте сервис** в `bot/services/`:

```python
# bot/services/payment.py
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.repository import UserRepository

async def process_payment(session: AsyncSession, user_id: int, amount: float) -> str:
    user = await UserRepository(session).get_by_telegram_id(user_id)
    # ... ваша логика
    return "Оплата прошла успешно"
```

**2. Вызовите из хендлера:**

```python
# bot/handlers/commands.py
from bot.services.payment import process_payment

@router.message(Command("pay"))
async def cmd_pay(message: Message) -> None:
    async with AsyncSessionFactory() as session:
        result = await process_payment(session, message.from_user.id, 100.0)
        await session.commit()
    await message.answer(result)
```

**3. Добавьте inline-кнопку** в `bot/keyboards/inline.py`:

```python
def payment_kb(amount: float) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text=f"💳 Оплатить {amount}₽",
        callback_data=f"pay:{amount}"
    ))
    return builder.as_markup()
```

**4. Обработайте callback** в `bot/handlers/callbacks.py`:

```python
@router.callback_query(F.data.startswith("pay:"))
async def cb_pay(callback: CallbackQuery) -> None:
    amount = float(callback.data.split(":")[1])
    # вызов сервиса...
    await callback.answer("Обработано!")
```

---

## 🗄️ Миграции базы данных

```bash
# Создать первую миграцию
alembic revision --autogenerate -m "initial"

# Применить
alembic upgrade head

# Откатить
alembic downgrade -1
```

Для добавления новой модели:
1. Добавьте класс в `bot/database/models.py` (наследуйте от `Base`)
2. `alembic revision --autogenerate -m "add my_model"`
3. `alembic upgrade head`

---

## 🐳 Запуск через Docker

```bash
# Локальная разработка (SQLite + Redis)
cd docker
docker compose up

# С PostgreSQL и Adminer
docker compose --profile dev up

# Production сборка
docker build -f docker/Dockerfile -t mybot:latest .
docker run --env-file .env mybot:latest
```

---

## 🌐 Деплой

### VPS (systemd)

```bash
# /etc/systemd/system/telegram-bot.service
[Unit]
Description=Telegram Bot
After=network.target

[Service]
User=botuser
WorkingDirectory=/opt/telegram-bot-template
EnvironmentFile=/opt/telegram-bot-template/.env
ExecStart=/opt/venv/bin/python -m bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable telegram-bot
systemctl start telegram-bot
```

### Railway / Render / Fly.io

1. Fork репозиторий
2. Создайте переменные окружения в дашборде платформы
3. Установите `BOT_MODE=webhook` и `WEBHOOK_HOST=https://ваш-домен.com`
4. Deploy — платформа автоматически запустит `python -m bot.main`

### Heroku

```bash
heroku create mybot
heroku config:set BOT_TOKEN=... BOT_MODE=webhook WEBHOOK_HOST=https://mybot.herokuapp.com
git push heroku main
```

---

## ✅ Чеклист перед production

- [ ] `BOT_TOKEN` только в переменных окружения, не в коде
- [ ] `ENVIRONMENT=production`, `LOG_JSON=true`
- [ ] `BOT_MODE=webhook` с HTTPS и `WEBHOOK_SECRET`
- [ ] `DATABASE_URL` указывает на PostgreSQL (не SQLite)
- [ ] Применены все миграции: `alembic upgrade head`
- [ ] `THROTTLE_RATE` настроен под вашу нагрузку
- [ ] Docker healthcheck работает: `curl /health`
- [ ] Настроен мониторинг (Sentry / Grafana)
- [ ] Резервное копирование БД

---

## 🧪 Тесты

```bash
pytest                  # все тесты
pytest tests/unit/      # только unit
pytest -v --tb=short    # verbose
```

---

## 📄 Лицензия

MIT
