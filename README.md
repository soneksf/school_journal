# Шкільний журнал (School Report Book)

Веб-застосунок на Django для ведення шкільного журналу: профілі учнів, вчителів, батьків та класів; виставлення оцінок (12-бальна шкала); фіксація пропусків; сповіщення учнів та батьків; AI-аналіз успішності на базі Anthropic Claude.

## Стек

- **Backend:** Django 5, Python 3.11+
- **БД:** PostgreSQL 16 (SQLite дозволено лише локально)
- **Черга задач:** Celery + Redis (асинхронні сповіщення, AI-задачі)
- **AI:** Anthropic Claude (`anthropic` SDK)
- **Веб-сервер:** Gunicorn + Nginx
- **Контейнеризація:** Docker + docker-compose

## Архітектура застосунків

| App | Відповідальність |
|---|---|
| `accounts` | Кастомна модель `User` з ролями, профілі вчителя/учня/батьків, аутентифікація, реєстрація |
| `school_core` | Класи, предмети, навчальні роки, уроки, призначення вчителів |
| `grades` | Виставлення та облік оцінок, табелі учнів |
| `attendance` | Облік пропусків |
| `notifications` | In-app + email сповіщення через Celery |
| `ai_assistant` | AI-аналіз успішності учня та чат-помічник через Anthropic API |

## Швидкий старт (Docker)

```bash
cp .env.example .env
# Згенерувати SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(50))"
# Вписати ключ в .env, додати ANTHROPIC_API_KEY за бажанням.

docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_demo   # опціонально — демо-дані
docker compose exec web python manage.py collectstatic --noinput
```

Застосунок відкриється на http://localhost/. Адмінка — http://localhost/admin/.

## Тести

```bash
python manage.py test
```

Або через pytest:

```bash
pip install pytest-django
pytest
```

## AI-агент

Реалізовано два сценарії:

1. **Аналіз успішності учня** — вчитель тригерить асинхронну задачу Celery, яка надсилає у Anthropic API структуровані дані про оцінки/пропуски учня і отримує JSON-висновок (`risk_level`, `summary`, `strengths`, `concerns`, `recommendations`). API-ключ — у env.
2. **Чат-помічник** — діалоговий інтерфейс для будь-якого користувача.

Файли: `ai_assistant/client.py`, `ai_assistant/tasks.py`, `ai_assistant/views.py`.
