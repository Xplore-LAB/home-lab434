#!/usr/bin/env bash
# AirSep Diagnose — 入口脚本（由 OpenClaw / Agent 调用）
#
# 用法：
#   bash run.sh read      --image dcs.png [--out /tmp/dcs_read.json]
#   bash run.sh store     --in /tmp/dcs_read.json
#   bash run.sh simulate  [--minutes 240] [--seed 42]
#   bash run.sh analyze   [--entity oxygen] [--metric purity]
#   bash run.sh causal    [--action valve_adjust]
#   bash run.sh export    [--outdir ./out]
#   bash run.sh report
#   bash run.sh full      --image dcs.png          # 端到端：读图 → 存 → 报告
#
# 环境变量：
#   ASMEMORY_HOME   asmemory 仓库路径（默认 ~/dsh-plugin-asmemory）
#   ASMEMORY_DB_PATH 记忆库路径（默认 ~/.asmemory/airsep-memory.db）
#   STEPFUN_API_KEY  StepFun 密钥（默认读 ~/.openclaw/secrets/stepfun.key）

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SKILL_DIR"

export ASMEMORY_HOME="${ASMEMORY_HOME:-$HOME/dsh-plugin-asmemory}"
export ASMEMORY_DB_PATH="${ASMEMORY_DB_PATH:-$HOME/.asmemory/airsep-memory.db}"
PY="${PYTHON:-python3}"

CMD="${1:-}"; shift || true

case "$CMD" in
  read)
    exec "$PY" dcs_read.py "$@"
    ;;
  store)
    exec "$PY" memory_io.py store "$@"
    ;;
  simulate)
    exec "$PY" memory_io.py simulate "$@"
    ;;
  analyze|trend)
    exec "$PY" diagnose.py trend "$@"
    ;;
  causal)
    exec "$PY" diagnose.py causal "$@"
    ;;
  summary)
    exec "$PY" diagnose.py summary "$@"
    ;;
  export)
    exec "$PY" diagnose.py export "$@"
    ;;
  report)
    exec "$PY" diagnose.py report "$@"
    ;;
  full)
    # 端到端：读图 → 写入记忆 → 诊断报告
    IMAGE=""
    OUT="$(mktemp -t dcs_read.XXXXXX.json)"
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --image) IMAGE="$2"; shift 2 ;;
        *) shift ;;
      esac
    done
    if [[ -z "$IMAGE" ]]; then
      echo "ERROR: full 需要 --image <path>" >&2
      exit 2
    fi
    echo "── ① 读图（StepFun 视觉）──"
    "$PY" dcs_read.py --image "$IMAGE" --out "$OUT"
    echo
    echo "── ② 写入时序记忆（asmemory）──"
    "$PY" memory_io.py store --in "$OUT"
    echo
    echo "── ③ 工况诊断报告 ──"
    "$PY" diagnose.py report
    ;;
  ""|-h|--help)
    sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    ;;
  *)
    echo "ERROR: 未知命令 '$CMD'（用 --help 看用法）" >&2
    exit 2
    ;;
esac
