#!/usr/bin/env bash
set -euo pipefail

# OpenClaw Probe - gather real OpenClaw state via CLI

STATUS_JSON=""
VERSION=""
GATEWAY_PID=""
GATEWAY_PORT=""

# Try to get status as JSON
if command -v openclaw >/dev/null 2>&1; then
  STATUS_JSON=$(openclaw status --all --json 2>/dev/null || openclaw status --json 2>/dev/null || echo "{}")
  VERSION=$(openclaw --version 2>/dev/null || openclaw version 2>/dev/null || echo "unknown")
fi

# Extract gateway PID from systemctl or ps
GATEWAY_PID=$(systemctl --user show openclaw-gateway.service 2>/dev/null | grep '^MainPID=' | cut -d= -f2 || \
               ps aux | grep -i '[o]penclaw.*gateway' | awk '{print $2}' | head -1 || echo "null")

# Extract port from status or default
GATEWAY_PORT=$(echo "$STATUS_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('gateway',{}).get('port','18789'))" 2>/dev/null || echo "18789")

# Get sessions via CLI
SESSIONS_JSON="[]"
if command -v openclaw >/dev/null 2>&1; then
  SESSIONS_JSON=$(openclaw sessions list --json 2>/dev/null || echo "[]")
fi

# Get processes
PROCESSES_JSON="[]"
PROCESSES_JSON=$(ps aux | awk 'NR>1 && /openclaw|node.*gateway|python.*mcp/ {print}' | while read -r line; do
  echo "$line" | awk '{printf "{\"user\":\"%s\",\"pid\":%s,\"cpu\":\"%s\",\"memory\":\"%s\",\"command\":\"%s\"}\n", $1, $2, $3, $4, $11}'
done | jq -s '.' 2>/dev/null || echo "[]")

cat <<EOF
{
  "probe": "openclaw",
  "timestamp": "$(date -Iseconds)",
  "version": "${VERSION}",
  "gateway": {
    "pid": ${GATEWAY_PID:-null},
    "port": ${GATEWAY_PORT:-18789}
  },
  "sessions": ${SESSIONS_JSON},
  "processes": ${PROCESSES_JSON},
  "raw_status": ${STATUS_JSON:-"{}"}
}
EOF
