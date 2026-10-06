#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Agent Toolkit - Workspace Governance & Cleanup
# ============================================================================
# Usage:
#   bash govern.sh --dry-run [TARGET_DIR]
#   bash govern.sh --apply [TARGET_DIR]
#
# Default TARGET_DIR: parent of this script (workspace root)
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_DIR="$(dirname "$SCRIPT_DIR")"
TODAY="$(date +%Y-%m-%d)"
REPORT="$TOOLKIT_DIR/memory/${TODAY}-govern-report.md"
LOG="$TOOLKIT_DIR/memory/${TODAY}-cleanup-log.md"
TRASH_DIR="$TOOLKIT_DIR/memory/trash"
DRY_RUN=true
TARGET_DIR=""

# ── Colors (disabled if not a tty) ────────────────────────────────────────────
if [ -t 1 ]; then
  C_RED='\033[0;31m'; C_YEL='\033[0;33m'; C_GRN='\033[0;32m'; C_RST='\033[0m'
else
  C_RED=''; C_YEL=''; C_GRN=''; C_RST=''
fi

# ── Helpers ───────────────────────────────────────────────────────────────────
usage() {
  sed -n '2,/^# ===+$/p' "$0" | sed 's/^# \?//'
  exit 1
}

log() { echo -e "${C_GRN}[INFO]${C_RST} $*"; }
warn() { echo -e "${C_YEL}[WARN]${C_RST} $*"; }
err() { echo -e "${C_RED}[ERR!]${C_RST} $*"; }

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --apply)   DRY_RUN=false; shift ;;
    -h|--help) usage ;;
    -*)        err "Unknown flag: $1"; usage ;;
    *)         TARGET_DIR="$1"; shift ;;
  esac
done

TARGET_DIR="${TARGET_DIR:-$(dirname "$TOOLKIT_DIR")}"
if [ ! -d "$TARGET_DIR" ]; then
  err "Target dir not found: $TARGET_DIR"; exit 1
fi

log "Target: $TARGET_DIR | Mode: $([ "$DRY_RUN" = true ] && echo DRY-RUN || echo APPLY)"

# ── Safety Policy ─────────────────────────────────────────────────────────────
MAX_FILES=200
MAX_BYTES=$((5 * 1024 * 1024 * 1024))  # 5GB
LARGE_FILE=$((100 * 1024 * 1024))       # 100MB

# ── Prepare report/log ────────────────────────────────────────────────────────
mkdir -p "$TOOLKIT_DIR/memory" "$TRASH_DIR"

cat > "$REPORT" <<EOF
# Governance Report - $TODAY

**Target:** \`$TARGET_DIR\`  
**Mode:** $([ "$DRY_RUN" = true ] && echo "dry-run" || echo "apply")  
**Time:** $(date '+%Y-%m-%d %H:%M:%S %Z')

## Summary

EOF

# Counters
declare -A CATEGORIES
CATEGORIES=([keep]=0 [review]=0 [trash]=0)
TRASH_FILES=()
TRASH_BYTES=0
declare -A SEEN_MD5

# ── Scan ──────────────────────────────────────────────────────────────────────
log "Scanning..."

while IFS= read -r -d '' f; do
  rel="${f#"$TARGET_DIR"/}"
  [ -z "$rel" ] && continue

  size=$(stat -c%s "$f" 2>/dev/null || echo 0)
  ext="${f##*.}"
  base="$(basename "$f")"

  # 1. Protected / whitelist
  if [[ "$rel" == .git/* || "$rel" == node_modules/* || "$rel" == .venv/* || \
        "$rel" == venv/* || "$rel" == dist/* || "$rel" == build/* || \
        "$rel" == .next/* || "$rel" == .idea/* || "$rel" == .vscode/* ]]; then
    category=keep; reason="protected_path"

  elif [[ "$rel" == memory/*.md || "$base" == *.key || "$base" == *.pem || \
          "$base" == *.env || "$base" == .env.* || "$base" == SOUL.md || \
          "$base" == USER.md || "$base" == MEMORY.md || "$base" == IDENTITY.md || \
          "$base" == DREAMS.md || "$base" == AGENTS.md || "$base" == FILE-MAP.md || \
          "$base" == README.md || "$base" == BEST_PRACTICES.md || "$base" == toolkit.json ]]; then
    category=keep; reason="core_file"

  # 2. Trash patterns
  elif [[ "$base" == .DS_Store || "$base" == Thumbs.db || "$base" == desktop.ini || \
          "$base" == *.tmp || "$base" == *.swp || "$base" == *.swo || "$base" == *.bak || \
          "$base" == *.cache || "$f" == *"/__pycache__/"* || "$ext" == "pyc" || "$ext" == "pyo" ]]; then
    category=trash; reason="junk_pattern"

  # 3. Old logs (>30d, >10MB)
  elif [[ "$ext" == "log" || "$f" == *"/logs/"* ]]; then
    if [ "$size" -gt $((10 * 1024 * 1024)) ]; then
      age=$(( ( $(date +%s) - $(stat -c %Y "$f") ) / 86400 ))
      if [ "$age" -gt 30 ]; then
        category=trash; reason="old_large_log"
      else
        category=review; reason="large_log"
      fi
    else
      category=review; reason="log_file"
    fi

  # 4. Large file protection
  elif [ "$size" -gt "$LARGE_FILE" ]; then
    category=review; reason="large_file_protection"

  # 5. Duplicate detection (md5)
  elif [ -s "$f" ]; then
    md5=$(md5sum "$f" | awk '{print $1}')
    if [[ -n "${SEEN_MD5[$md5]+x}" ]]; then
      category=review; reason="duplicate"
    else
      SEEN_MD5[$md5]="$rel"
      category=keep; reason="unique"
    fi

  else
    category=keep; reason="default"
  fi

  CATEGORIES[$category]=$(( ${CATEGORIES[$category]} + 1 ))

  if [ "$category" = "trash" ]; then
    TRASH_FILES+=("$rel")
    TRASH_BYTES=$(( TRASH_BYTES + size ))
  fi

done < <(find "$TARGET_DIR" -type f -print0 2>/dev/null | sort -z)

# ── Report ────────────────────────────────────────────────────────────────────
{
  echo "| Category | Count |"
  echo "|----------|-------|"
  for cat in keep review trash; do
    printf '| %-8s | %5s |\n' "$cat" "${CATEGORIES[$cat]}"
  done
  echo ""
  echo "## Trash Candidates ($((${#TRASH_FILES[@]})) files, $(numfmt --to=iec $TRASH_BYTES 2>/dev/null || echo ${TRASH_BYTES} bytes))"
  echo ""
  echo "| File | Reason | Size |"
  echo "|------|--------|------|"
  for rel in "${TRASH_FILES[@]}"; do
    size=$(stat -c%s "$TARGET_DIR/$rel" 2>/dev/null || echo 0)
    human=$(numfmt --to=iec $size 2>/dev/null || echo "${size}B")
    # extract reason from logic above (simplified)
    reason="junk_pattern"
    echo "| \`$rel\` | $reason | $human |"
  done
} >> "$REPORT"

cat >> "$REPORT" <<EOF

## Limits Check

- Max files per run: $MAX_FILES
- Max bytes per run: $(numfmt --to=iec $MAX_BYTES 2>/dev/null || echo ${MAX_BYTES})
- Large file threshold: $(numfmt --to=iec $LARGE_FILE 2>/dev/null || echo ${LARGE_FILE})
- Proposed trash files: ${#TRASH_FILES[@]}
- Proposed trash bytes: $(numfmt --to=iec $TRASH_BYTES 2>/dev/null || echo ${TRASH_BYTES})

EOF

log "Report written to $REPORT"
cat "$REPORT"

# ── Apply ─────────────────────────────────────────────────────────────────────
if [ "$DRY_RUN" = true ]; then
  log "Dry-run complete. Re-run with --apply to execute."
  exit 0
fi

if [ ${#TRASH_FILES[@]} -eq 0 ]; then
  log "Nothing to clean. Exiting."
  exit 0
fi

if [ ${#TRASH_FILES[@]} -gt $MAX_FILES ]; then
  err "Refusing: ${#TRASH_FILES[@]} files exceeds limit of $MAX_FILES"
  exit 1
fi

if [ "$TRASH_BYTES" -gt "$MAX_BYTES" ]; then
  err "Refusing: $(numfmt --to=iec $TRASH_BYTES) exceeds limit of $(numfmt --to=iec $MAX_BYTES)"
  exit 1
fi

warn "About to move ${#TRASH_FILES[@]} files to trash ($(numfmt --to=iec $TRASH_BYTES))"
read -rp "Proceed? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  log "Aborted by user."
  exit 0
fi

mkdir -p "$TRASH_DIR/$TODAY"
moved=0
{
  echo "# Cleanup Log - $TODAY"
  echo "_Time: $(date '+%Y-%m-%d %H:%M:%S %Z')_"
  echo ""
} > "$LOG"

for rel in "${TRASH_FILES[@]}"; do
  src="$TARGET_DIR/$rel"
  dst="$TRASH_DIR/$TODAY/$rel"
  mkdir -p "$(dirname "$dst")"

  if mv -f "$src" "$dst" 2>/dev/null; then
    size=$(stat -c%s "$src" 2>/dev/null || stat -c%s "$dst" 2>/dev/null || echo 0)
    echo "- \`$rel\` → \`trash/$TODAY/$rel\` ($(numfmt --to=iec $size 2>/dev/null || echo ${size}B))" >> "$LOG"
    moved=$((moved + 1))
  else
    warn "Failed to move: $rel"
  fi
done

log "Moved $moved files to trash."
log "Log: $LOG"
log "Restore (if needed): cp -r $TRASH_DIR/$TODAY/* \"$TARGET_DIR/\""
