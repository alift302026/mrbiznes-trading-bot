#!/usr/bin/env bash
# ============================================================
# MRBIZNES — PLT Range Scanner cron installer (IDEMPOTENT)
# Installs/updates ONE cron entry: every hour at minute 5.
# Never creates duplicate jobs: previous matching lines
# (marker OR script name) are removed before adding.
#
# Env overrides:
#   PYTHON_BIN   default /usr/bin/python3
#   CRONTAB_BIN  default "crontab" (e.g. "busybox crontab")
# ============================================================
set -euo pipefail

SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/plt_range_scanner.py"
LOG_DIR="$(cd "$(dirname "$0")" && pwd)/logs"
LOG_PATH="$LOG_DIR/plt_range_scanner.log"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"
CRONTAB_BIN="${CRONTAB_BIN:-crontab}"
MARKER="# MRBIZNES-PLT-RANGE-SCANNER"
CRON_LINE="5 * * * * $PYTHON_BIN $SCRIPT_PATH >> $LOG_PATH 2>&1 $MARKER"

# --- validation -------------------------------------------------
[[ -f "$SCRIPT_PATH" ]] || { echo "ERROR: $SCRIPT_PATH not found"; exit 1; }
[[ -x "$PYTHON_BIN" ]] || { echo "ERROR: python not found at $PYTHON_BIN"; exit 1; }
"$PYTHON_BIN" "$SCRIPT_PATH" --selftest || { echo "ERROR: selftest failed — cron NOT installed"; exit 1; }
mkdir -p "$LOG_DIR"

# --- idempotent install ------------------------------------------
CURRENT="$($CRONTAB_BIN -l 2>/dev/null || true)"
CLEANED="$(printf '%s\n' "$CURRENT" | grep -vF "$MARKER" | grep -vF "plt_range_scanner.py" || true)"
printf '%s\n%s\n' "$CLEANED" "$CRON_LINE" | $CRONTAB_BIN -

# --- verify ------------------------------------------------------
echo "---- installed crontab ----"
$CRONTAB_BIN -l
COUNT="$($CRONTAB_BIN -l 2>/dev/null | grep -cF "plt_range_scanner.py" || true)"
echo "---------------------------"
echo "plt_range_scanner cron entries: $COUNT (must be 1)"
[[ "$COUNT" == "1" ]] || { echo "ERROR: duplicate cron entries detected"; exit 1; }
echo "OK — PLT Range Scanner scheduled at minute 5 of every hour."
