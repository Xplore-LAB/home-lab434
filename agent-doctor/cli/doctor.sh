#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCTOR_DIR="$(dirname "$SCRIPT_DIR")"
WORKSPACE="${DOCTOR_DIR}/.."

# Colors
if [ -t 1 ]; then
  C_RED='\033[0;31m'; C_YEL='\033[0;33m'; C_GRN='\033[0;32m'; C_BLD='\033[1m'; C_RST='\033[0m'
else
  C_RED=''; C_YEL=''; C_GRN=''; C_BLD=''; C_RST=''
fi

usage() {
  cat <<EOF
${C_BLD}Agent Doctor${C_RST} - Agent Harness Diagnostic Tool

Usage:
  doctor.sh <command> [options]

Commands:
  status      Show system health overview
  diagnose    Run full diagnosis
  agents      List all agents and their status
  inspect     Inspect specific agent/session/process
  report      Generate diagnostic report
  ui          Launch web GUI (placeholder)
  help        Show this help

Examples:
  doctor.sh status
  doctor.sh diagnose
  doctor.sh agents
  doctor.sh inspect agent:main
  doctor.sh report
EOF
  exit 0
}

# Ensure Python deps
python3 -c "import yaml" 2>/dev/null || pip install -q pyyaml 2>/dev/null || true

# Run Python core
run_core() {
  python3 - "${WORKSPACE}" "$@" <<'PY'
import sys
import json
from pathlib import Path

workspace = Path(sys.argv[1])
doctor_dir = workspace / "agent-doctor"
sys.path.insert(0, str(doctor_dir / "core"))

from state import ProbeRunner, StateStore, DiagnosticEngine, Reconciler

cmd = sys.argv[2] if len(sys.argv) > 2 else "full"

runner = ProbeRunner(workspace)
store = StateStore()
engine = DiagnosticEngine(store)

probes = runner.collect_all()
reconciler = Reconciler(store)
reconciler.reconcile(probes)
issues = engine.run_builtin_checks()
for issue in issues:
    store.add_issue(issue)

if cmd == "status":
    issues_list = store.issues
    crit = sum(1 for i in issues_list if i.severity == "critical")
    warn = sum(1 for i in issues_list if i.severity == "warning")
    info = sum(1 for i in issues_list if i.severity == "info")
    print(json.dumps({
        "health": "healthy" if crit == 0 and warn == 0 else "degraded" if crit == 0 else "critical",
        "issues": {"critical": crit, "warning": warn, "info": info}
    }, indent=2))
elif cmd == "agents":
    print(json.dumps({"agents": [asdict(a) for a in store.agents.values()]}, indent=2))
elif cmd == "issues":
    print(json.dumps({"issues": [asdict(i) for i in store.issues]}, indent=2))
else:
    print(json.dumps({"state": store.to_dict(), "probes": probes}, indent=2))
PY
}

# Commands
case "${1:-help}" in
  status)
    run_core status
    ;;
  diagnose|agents|inspect|report)
    shift
    run_core "$@"
    ;;
  ui)
    echo "GUI not yet implemented. Use CLI for now."
    echo "Future: doctor.sh ui will launch web interface on 127.0.0.1:8080"
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    echo "Unknown command: $1"
    usage
    ;;
esac
