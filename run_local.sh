#!/usr/bin/env bash
# ============================================================
#  اجرای ربات MrBiznes روی کامپیوتر خودتان (لینوکس / مک)
#     bash run_local.sh
# ============================================================

set -e

cd "$(dirname "$0")"

echo "=============================================="
echo "   MrBiznes — اجرای محلی"
echo "=============================================="

if [ ! -d ".venv" ]; then
    echo "▶ ساخت محیط پایتون…"
    python3 -m venv .venv
fi

echo "▶ نصب پیش‌نیازها…"
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

if [ ! -f ".env" ]; then
    echo "▶ ساخت فایل .env از نمونه…"
    cp .env.example .env
    echo
    echo "⚠️  فایل .env ساخته شد. حالا BOT_TOKEN و ADMIN_IDS را داخلش بگذارید:"
    echo "     nano .env"
    echo
fi

echo "▶ چک کردن وضعیت…"
.venv/bin/python scripts/doctor.py || true

echo
echo "▶ روشن کردن ربات (برای توقف: Ctrl+C)"
echo
exec .venv/bin/python main.py
