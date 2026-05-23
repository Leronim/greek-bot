# Greek A1 Telegram Trainer

Telegram bot for learning Greek A1 vocabulary with written answers, soft answer checking, spaced repetition, statistics, and JSON import.

## Stack

- Python
- aiogram 3
- SQLAlchemy 2 async
- SQLite for MVP
- Alembic
- Docker-ready structure

Python 3.12+ is supported. For Python 3.14, use the pinned dependency versions from `requirements.txt`; older `pydantic-core` releases do not build against 3.14.

## Quick Start

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.main
```

Before running, put your Telegram bot token into `.env`.

## Import Seed Words

The bot imports `data/words_a1.json` automatically on startup if the database has no words.

Manual import is available in Telegram for admins:

```text
/admin_import
```

Then send a JSON file in the same format as `data/words_a1.json`.

## MVP Features

- Main menu with buttons
- Written answer mode
- Russian to Greek, Greek to Russian, mixed direction
- Soft normalization for Greek and Russian
- 4-choice quiz
- Lesson cards
- Review cards
- Spaced repetition boxes
- Hard words
- Basic progress stats
- JSON word import

## Dictionary Admin Panel

Run locally:

```bash
uvicorn app.admin_web.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and log in with `ADMIN_WEB_PASSWORD` from `.env`.

On the server, keep it bound to `127.0.0.1` and expose it through Nginx + HTTPS or an SSH tunnel.

## Auto Deploy

Pushes to `main` can deploy automatically through GitHub Actions. Add these repository secrets:

- `DEPLOY_HOST`: server IP, for example `46.225.185.193`
- `DEPLOY_USER`: usually `root`
- `DEPLOY_PORT`: usually `22`
- `DEPLOY_PATH`: usually `/root/greek-bot`
- `DEPLOY_SSH_KEY`: private SSH key that can connect to the server

The workflow uploads the code, preserves `.env`, `greek_bot.db`, and `.venv`, installs dependencies, runs migrations, and restarts `greek-bot.service`.
It also syncs `greek_bot.db` with `data/words_a1.json`, so dictionary changes from GitHub are applied automatically on deploy.

Manual dictionary sync:

```bash
python -m app.scripts.sync_dictionary
```
