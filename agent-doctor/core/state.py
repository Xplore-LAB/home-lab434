#!/usr/bin/env python3
"""
Agent Doctor - State Reconciliation Engine
Merges probes, adapters, and system state into unified graph.
"""

import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class Agent:
    id: str
    name: str
    status: str = "unknown"
    model: Optional[str] = None
    session_id: Optional[str] = None
    parent_id: Optional[str] = None
    last_progress: Optional[str] = None
    task: Optional[str] = None


@dataclass
class Session:
    id: str
    agent_id: Optional[str]
    status: str
    created_at: Optional[str]
    last_activity: Optional[str]
    message_count: int = 0
    model: Optional[str] = None


@dataclass
class Process:
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    cmdline: str
    parent_pid: Optional[int] = None
    agent_id: Optional[str] = None


@dataclass
class Issue:
    id: str
    severity: str
    category: str
    title: str
    symptoms: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    root_cause: Optional[str] = None
    confidence: str = "medium"
    impact: Optional[str] = None
    repair: Optional[str] = None
    risk: str = "safe"
    rollback_available: bool = True
    status: str = "open"


class StateStore:
    def __init__(self):
        self.agents: dict = {}
        self.sessions: dict = {}
        self.processes: dict = {}
        self.issues: list = []
        self.raw_probes: dict = {}

    def add_agent(self, agent: Agent):
        self.agents[agent.id] = agent

    def add_session(self, session: Session):
        self.sessions[session.id] = session

    def add_process(self, process: Process):
        self.processes[process.pid] = process

    def add_issue(self, issue: Issue):
        self.issues.append(issue)

    def to_dict(self):
        return {
            "agents": [asdict(a) for a in self.agents.values()],
            "sessions": [asdict(s) for s in self.sessions.values()],
            "processes": [asdict(p) for p in self.processes.values()],
            "issues": [asdict(i) for i in self.issues],
        }


class ProbeRunner:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.doctor_dir = workspace / "agent-doctor"

    def run_probe(self, name: str) -> dict:
        script = self.doctor_dir / "probes" / f"{name}.sh"
        if not script.exists():
            return {"error": f"probe not found: {name}"}

        try:
            result = subprocess.run(
                [str(script)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                return {"error": f"probe failed: {result.stderr}"}
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": str(e)}

    def collect_all(self) -> dict:
        probes = {}
        for name in ["system", "openclaw"]:
            probes[name] = self.run_probe(name)
        return probes


class Reconciler:
    def __init__(self, store: StateStore):
        self.store = store

    def reconcile(self, probes: dict):
        self.store.raw_probes = probes
        openclaw = probes.get("openclaw", {})

        # Parse sessions
        for s in openclaw.get("sessions", []):
            sid = s.get("key") or s.get("id") or s.get("session_id")
            if not sid:
                continue
            session = Session(
                id=sid,
                agent_id=s.get("agent") or s.get("agent_id"),
                status=s.get("status", "unknown"),
                created_at=s.get("created_at") or s.get("started_at"),
                last_activity=s.get("last_activity") or s.get("updated_at"),
                message_count=s.get("message_count", 0),
                model=s.get("model") or s.get("model_name"),
            )
            self.store.add_session(session)

        # Parse processes
        for p in openclaw.get("processes", []):
            try:
                pid = int(p.get("pid", 0))
                if pid <= 0:
                    continue
                process = Process(
                    pid=pid,
                    name=p.get("command", "unknown").split()[0],
                    cpu_percent=float(p.get("cpu", 0) or 0),
                    memory_mb=float(p.get("memory", "0").replace("M", "").replace("G", "") or 0),
                    cmdline=p.get("command", ""),
                )
                self.store.add_process(process)
            except Exception:
                continue


class DiagnosticEngine:
    def __init__(self, store: StateStore):
        self.store = store

    def run_builtin_checks(self) -> List[Issue]:
        issues = []

        # System resource checks
        system = self.store.raw_probes.get("system", {})

        # Memory
        mem_total = system.get("memory", {}).get("total_mb", 0)
        mem_avail = system.get("memory", {}).get("available_mb", 0)
        if mem_total > 0:
            usage_pct = ((mem_total - mem_avail) / mem_total) * 100
            if usage_pct > 90:
                issues.append(Issue(
                    id="SYS-001",
                    severity="warning",
                    category="resources",
                    title="High Memory Usage",
                    symptoms=[f"Memory usage at {usage_pct:.1f}%"],
                    evidence=[f"Total: {mem_total}MB, Available: {mem_avail}MB"],
                    root_cause="System memory pressure",
                    confidence="high",
                    impact="May cause OOM or swapping",
                    repair="Check for memory leaks in long-running processes",
                    risk="safe"
                ))

        # Disk
        disk_usage = system.get("disk", {}).get("usage", "0%")
        if disk_usage.endswith("%"):
            disk_pct = int(disk_usage.rstrip("%"))
            if disk_pct > 80:
                issues.append(Issue(
                    id="SYS-002",
                    severity="warning" if disk_pct < 95 else "critical",
                    category="resources",
                    title="High Disk Usage",
                    symptoms=[f"Disk at {disk_usage}"],
                    evidence=[f"Free space: {system.get('disk', {}).get('free', 'unknown')}"],
                    root_cause="Disk space running low",
                    confidence="high",
                    impact="May prevent writes, logs, checkpoints",
                    repair="Clean old logs, transcripts, checkpoints",
                    risk="safe"
                ))

        # OpenClaw checks
        openclaw = self.store.raw_probes.get("openclaw", {})
        gateway = openclaw.get("gateway", {})

        # Gateway not running
        if not gateway.get("pid") or gateway.get("pid") == "null":
            issues.append(Issue(
                id="OC-001",
                severity="critical",
                category="gateway",
                title="Gateway Not Running",
                symptoms=["Gateway PID not found"],
                evidence=[f"PID: {gateway.get('pid')}"],
                root_cause="Gateway process not detected",
                confidence="high",
                impact="All OpenClaw services unavailable",
                repair="Start gateway: systemctl --user start openclaw-gateway",
                risk="safe"
            ))

        # Session checks
        sessions = list(self.store.sessions.values())
        if len(sessions) > 0:
            # Check for sessions with high message count (possible context bloat)
            for sid, session in self.store.sessions.items():
                if session.message_count > 1000:
                    issues.append(Issue(
                        id="OC-002",
                        severity="info",
                        category="session",
                        title=f"Large Session: {sid}",
                        symptoms=[f"Session has {session.message_count} messages"],
                        evidence=[f"Session ID: {sid}"],
                        root_cause="Long-running session, possible context bloat",
                        confidence="medium",
                        impact="May slow down responses, increased token usage",
                        repair="Consider compacting or starting new session",
                        risk="safe"
                    ))

        return issues
