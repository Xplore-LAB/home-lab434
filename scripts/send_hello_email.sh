#!/usr/bin/env bash
# Send the "你好" greeting email from 1228626521@qq.com to itself.
# The SMTP authorization code is read from a 0600 file staged by the user
# in their own terminal; it never appears in chat, logs, or argv.
set -euo pipefail

AUTH_FILE="${AUTH_FILE:-$HOME/.qq_smtp_authcode}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -s "$AUTH_FILE" ]]; then
  echo "ERROR: auth code file missing or empty: $AUTH_FILE" >&2
  exit 2
fi
if [[ "$(stat -c '%a' "$AUTH_FILE")" != "600" ]]; then
  echo "ERROR: $AUTH_FILE must be mode 600 (got $(stat -c '%a' "$AUTH_FILE"))" >&2
  exit 2
fi

SMTP_HOST=smtp.qq.com \
SMTP_PORT=465 \
SMTP_USER=1228626521@qq.com \
SMTP_AUTH="$(cat "$AUTH_FILE")" \
MAIL_FROM=1228626521@qq.com \
MAIL_TO=1228626521@qq.com \
MAIL_SUBJECT=你好 \
MAIL_BODY=你好 \
python3 "$SCRIPT_DIR/send_smtp_email.py"
