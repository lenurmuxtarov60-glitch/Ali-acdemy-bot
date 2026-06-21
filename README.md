# ALI ACADEMY BOT

Python Telegram bot for admin attendance and parent notifications.

## Local setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values.

```bash
python run.py
```

## Railway deploy

This repository is ready for Railway deployment.

1. Create a new Railway project from GitHub.
2. Add PostgreSQL.
3. Set these environment variables:
   - `ADMIN_BOT_TOKEN`
   - `PARENT_BOT_TOKEN`
   - `PARENT_BOT_USERNAME`
   - `SUPER_ADMIN_ID`
   - `DATABASE_URL`
   - `MAIN_TEACHER`
   - `CENTER_NAME`

Railway will run `python run.py` automatically using `Procfile` / `railway.json`.

> Note: run only one bot service in Railway to avoid duplicate messages.

## Ishlatish

### Admin (@Ali_Academy_bot)
1. `/start` — admin panel
2. **O'quvchilar** → ism-familiya qo'shing
3. Ota-ona so'rovi kelganda **Keldi / Kelmadi** bosing

### Ota-ona (@ali_davom_bot)
1. Farzand **ism-familiyasini** yozing
2. Admin tasdiqlagach javob keladi

## Texnologiyalar

Python 3.11 · python-telegram-bot 21 · SQLAlchemy · PostgreSQL / SQLite
