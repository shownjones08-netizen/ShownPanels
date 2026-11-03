#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
#  QURESHIxOTP Bot — one-command starter
#  Usage:  ./start.sh            (polling mode)
#          WEBHOOK_URL=... ./start.sh   (webhook mode)
# ══════════════════════════════════════════════════════════════
set -euo pipefail

cd "$(dirname "$0")"

PY="${PYTHON_BIN:-python3}"

echo "▶ Installing / verifying requirements…"
"$PY" -m pip install --quiet --upgrade pip
"$PY" -m pip install --quiet -r requirements.txt

echo "▶ Starting QURESHIxOTP bot…"
exec "$PY" shownXpannel.py
