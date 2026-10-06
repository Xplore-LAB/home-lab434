#!/usr/bin/env bash
set -euo pipefail

# System Probe - gather OS/process/disk state

MEM_INFO=$(free -m 2>/dev/null || echo "0 0 0 0")
MEM_TOTAL=$(echo "$MEM_INFO" | awk '/^Mem:/ {print $2}')
MEM_AVAIL=$(echo "$MEM_INFO" | awk '/^Mem:/ {print $7}')

DISK_LINE=$(df -h /home/lab434 2>/dev/null | awk 'NR==2 {print $5, $4}' || echo "N/A N/A")
DISK_USAGE=$(echo "$DISK_LINE" | awk '{print $1}')
DISK_FREE=$(echo "$DISK_LINE" | awk '{print $2}')

CPU_LOAD=$(uptime 2>/dev/null | awk -F'load average:' '{print $2}' | xargs || echo "unknown")

PROC_OPENCLAW=$(ps aux 2>/dev/null | grep -i openclaw | grep -v grep | wc -l || echo 0)
PROC_PYTHON=$(ps aux 2>/dev/null | grep -i python | grep -v grep | wc -l || echo 0)
PROC_NODE=$(ps aux 2>/dev/null | grep -i node | grep -v grep | wc -l || echo 0)

cat <<EOF
{
  "probe": "system",
  "timestamp": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "memory": {
    "total_mb": ${MEM_TOTAL:-0},
    "available_mb": ${MEM_AVAIL:-0}
  },
  "disk": {
    "usage": "${DISK_USAGE:-N/A}",
    "free": "${DISK_FREE:-N/A}"
  },
  "cpu": {
    "load_avg": "${CPU_LOAD:-unknown}"
  },
  "processes": {
    "openclaw": ${PROC_OPENCLAW},
    "python": ${PROC_PYTHON},
    "node": ${PROC_NODE}
  }
}
EOF
