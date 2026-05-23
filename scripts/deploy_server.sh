#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${DEPLOY_PATH:-/root/greek-bot}"
RELEASE_ARCHIVE="/tmp/greek-bot-release.tar.gz"
SERVICE_NAME="${SERVICE_NAME:-greek-bot}"

if [ ! -f "$RELEASE_ARCHIVE" ]; then
  echo "Release archive not found: $RELEASE_ARCHIVE" >&2
  exit 1
fi

mkdir -p "$APP_DIR"

if [ -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env" /tmp/greek-bot.env.backup
fi
if [ -f "$APP_DIR/greek_bot.db" ]; then
  cp "$APP_DIR/greek_bot.db" /tmp/greek_bot.db.backup
fi
if [ -d "$APP_DIR/data/audio" ]; then
  rm -rf /tmp/greek-bot-audio.backup
  cp -a "$APP_DIR/data/audio" /tmp/greek-bot-audio.backup
fi

for item in "$APP_DIR"/* "$APP_DIR"/.[!.]* "$APP_DIR"/..?*; do
  [ -e "$item" ] || continue
  case "$(basename "$item")" in
    .env|greek_bot.db|.venv)
      continue
      ;;
  esac
  rm -rf "$item"
done

tar -xzf "$RELEASE_ARCHIVE" -C "$APP_DIR"

if [ -f /tmp/greek-bot.env.backup ]; then
  mv /tmp/greek-bot.env.backup "$APP_DIR/.env"
fi
if [ -f /tmp/greek_bot.db.backup ]; then
  mv /tmp/greek_bot.db.backup "$APP_DIR/greek_bot.db"
fi
if [ -d /tmp/greek-bot-audio.backup ]; then
  mkdir -p "$APP_DIR/data"
  rm -rf "$APP_DIR/data/audio"
  mv /tmp/greek-bot-audio.backup "$APP_DIR/data/audio"
fi

cd "$APP_DIR"

if ! python3 -m venv --help >/dev/null 2>&1; then
  apt-get update
  apt-get install -y python3 python3-venv python3-pip
fi

if [ ! -x ".venv/bin/python" ]; then
  rm -rf .venv
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python -m app.scripts.sync_dictionary
.venv/bin/python -m app.scripts.generate_audio || echo "Audio generation failed, deploy continues."

systemctl restart "$SERVICE_NAME"
systemctl --no-pager --full status "$SERVICE_NAME"
