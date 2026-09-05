#!/usr/bin/env bash
# ============================================================
# PLT Range Scanner — cron installer (run ON THE SERVER)
# ============================================================
# Creates the hourly cron entry (minute 5), guarded against
# duplicates.  Default schedule:  5 * * * *   (every hour)
# Pass  --every-2h  to use:       5 */2 * * *
#
# Usage:
#   ./install_plt_range_cron.sh [--every-2h] [--python /path/to/python]
# ============================================================
set -euo pipefail

cd "$(dirname "$0")"
REPO_DIR="$(pwd)"
SCANNER="$REPO_DIR/plt_range_scanner.py"
LOG_DIR="$REPO_DIR/data/plt_range"
LOG_FILE="$LOG_DIR/plt_range_scanner.log"
MARKER="# PLT-RANGE-SCANNER"

PYTHON_BIN=""
EVERY_2H=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --every-2h) EVERY_2H=1 ;;
        --python) PYTHON_BIN="$2"; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
    shift
done

echo "==> PLT Range Scanner installer"
echo "    repo : $REPO_DIR"

# ------------------------------------------------------------
# 1. Scanner script exists?
# ------------------------------------------------------------
if [[ ! -f "$SCANNER" ]]; then
    echo "ERROR: $SCANNER not found" >&2
    exit 1
fi
echo "    scanner: OK ($SCANNER)"

# ------------------------------------------------------------
# 2. Python interpreter
# ------------------------------------------------------------
if [[ -z "$PYTHON_BIN" ]]; then
    for cand in "$REPO_DIR/.venv/bin/python" "$REPO_DIR/venv/bin/python"; do
        if [[ -x "$cand" ]]; then PYTHON_BIN="$cand"; break; fi
    done
fi
if [[ -z "$PYTHON_BIN" ]]; then PYTHON_BIN="$(command -v python3 || true)"; fi
if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
    echo "ERROR: no python3 found (use --python)" >&2
    exit 1
fi
echo "    python : $PYTHON_BIN"

# ------------------------------------------------------------
# 3. Dependencies (requests + optional Pillow)
# ------------------------------------------------------------
"$PYTHON_BIN" -c "import requests" 2>/dev/null \
    || { echo "ERROR: 'requests' missing for $PYTHON_BIN" >&2; exit 1; }
echo "    requests: OK"
if "$PYTHON_BIN" -c "import PIL" 2>/dev/null; then
    echo "    pillow: OK (cards enabled)"
else
    echo "    pillow: missing (text-only posts; cards skipped)"
fi

# ------------------------------------------------------------
# 4. Config (.env with TELEGRAM_BOT_TOKEN / PLT_RANGE_CHANNEL_ID)
# ------------------------------------------------------------
if [[ -f "$REPO_DIR/.env" ]] && grep -q "TELEGRAM_BOT_TOKEN=" "$REPO_DIR/.env" && grep -q "PLT_RANGE_CHANNEL_ID=" "$REPO_DIR/.env"; then
    echo "    .env channel config: present"
else
    echo "    WARNING: .env missing TELEGRAM_BOT_TOKEN or PLT_RANGE_CHANNEL_ID ->"
    echo "             results will be written to files only (no channel post)."
fi

# ------------------------------------------------------------
# 5. cron available?
# ------------------------------------------------------------
if ! command -v crontab >/dev/null 2>&1; then
    echo "WARNING: crontab not found; attempting to install cron ..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -qq && sudo apt-get install -y -qq cron
        sudo service cron start || sudo /etc/init.d/cron start || true
    else
        echo "ERROR: install cron manually, then re-run this script." >&2
        exit 1
    fi
fi

# ------------------------------------------------------------
# 6. Register entry (no duplicates)
# ------------------------------------------------------------
mkdir -p "$LOG_DIR"

if [[ $EVERY_2H -eq 1 ]]; then
    SCHED="5 */2 * * *"
else
    SCHED="5 * * * *"
fi

ENTRY="$SCHED $PYTHON_BIN $SCANNER >> $LOG_FILE 2>&1"

crontab -l >/tmp/plt_cron_backup.txt 2>/dev/null || true

# Drop any previous PLT-RANGE-SCANNER lines (idempotent re-run)
grep -v "$MARKER" /tmp/plt_cron_backup.txt > /tmp/plt_cron_new.txt || true

{
    cat /tmp/plt_cron_new.txt
    echo "$ENTRY  $MARKER"
} | crontab -

echo ""
echo "==> Installed cron entry:"
echo "    $ENTRY"
echo ""
echo "    schedule: $SCHED"
echo "    log file : $LOG_FILE"
echo ""
echo "==> Verify with:  crontab -l"
echo "    To remove:    crontab -l | grep -v '$MARKER' | crontab -"
