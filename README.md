# ALI ACADEMY — Davomat Bot

Ikkita Telegram bot:
- **Admin bot** — o'quvchilar, davomat, hisobotlar
- **Ota-ona bot** — farzand ismi yozib davomat so'rash

## Tez boshlash (lokal)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

`.env` faylini to'ldiring:

```env
ADMIN_BOT_TOKEN=admin_bot_token
PARENT_BOT_TOKEN=ota_ona_bot_token
PARENT_BOT_USERNAME=ali_davom_bot
SUPER_ADMIN_ID=sizning_telegram_id
DATABASE_URL=sqlite:///davomat.db
MAIN_TEACHER=Nodirbek
CENTER_NAME=ALI ACADEMY
```

```bash
python run.py
```

## Railway ga deploy

### 1. Loyihani Railway ga ulang
1. [railway.app](https://railway.app) → **New Project**
2. **Deploy from GitHub** yoki papkani yuklang

### 2. PostgreSQL qo'shing
- **+ New** → **Database** → **PostgreSQL**
- PostgreSQL servisidagi `DATABASE_URL` ni bot servisiga ulang

### 3. Muhit o'zgaruvchilari (Variables)

| O'zgaruvchi | Tavsif |
|---|---|
| `ADMIN_BOT_TOKEN` | Admin panel bot tokeni |
| `PARENT_BOT_TOKEN` | Ota-ona bot tokeni |
| `PARENT_BOT_USERNAME` | Ota-ona bot username (masalan: `ali_davom_bot`) |
| `SUPER_ADMIN_ID` | Sizning Telegram ID |
| `DATABASE_URL` | PostgreSQL URL (Railway avtomatik beradi) |
| `MAIN_TEACHER` | Asosiy o'qituvchi ismi |
| `CENTER_NAME` | Markaz nomi |

### 4. Deploy
Railway avtomatik `python run.py` ni ishga tushiradi (`Procfile` / `railway.json`).

> **Muhim:** Faqat **bitta** Railway servisida bot ishlating. Ikki nusxa ishga tushsa, xabarlar takrorlanadi.

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
