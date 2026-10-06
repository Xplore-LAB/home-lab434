#!/usr/bin/env python3
"""
OpenClaw Adapter - Bridge between Agent Doctor and OpenClaw
Provides unified interface to query OpenClaw state.
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Optional


class OpenClawAdapter:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.openclaw_dir = workspace / ".openclaw"
        self.config_file = self.openclaw_dir / "config.json"
        self.session_store = self.openclaw_dir / "sessions"

    def detect(self) -> dict:
        """Detect OpenClaw installation and version."""
        result = {
            "installed": False,
            "version": None,
            "workspace": str(self.workspace),
            "config_exists": self.config_file.exists(),
            "session_store_exists": self.session_store.exists()
        }

        # Try to get version
        try:
            version = subprocess.check_output(
                ["openclaw", "--version"],
                text=True,
                timeout=5
            ).strip()
            result["version"] = version
            result["installed"] = True
        except Exception:
            # Try alternative
            try:
                version = subprocess.check_output(
                    ["openclaw", "version"],
                    text=True,
                    timeout=5
                ).strip()
                result["version"] = version
                result["installed"] = True
            except Exception:
                pass

        return result

    def get_config(self) -> dict:
        """Read OpenClaw configuration."""
        if not self.config_file.exists():
            return {"error": "config not found"}

        try:
            with open(self.config_file) as f:
                return json.load(f)
        except Exception as e:
            return {"error": str(e)}

    def list_sessions(self) -> list[dict]:
        """List all sessions from session store."""
        sessions = []

        # Try CLI first
        try:
            output = subprocess.check_output(
                ["openclaw", "sessions", "list", "--json"],
                text=True,
                timeout=10
            )
            data = json.loads(output)
            if isinstance(data, list):
                sessions = data
            elif isinstance(data, dict):
                sessions = data.get("sessions", [])
        except Exception:
            # Fallback: parse session files
            if self.session_store.exists():
                for f in self.session_store.glob("*.json"):
                    try:
                        with open(f) as fp:
                            sessions.append(json.load(fp))
                    except Exception:
                        pass

        return sessions

    def get_session_detail(self, session_id: str) -> dict:
        """Get detailed session info."""
        try:
            output = subprocess.check_output(
                ["openclaw", "sessions", "show", session_id, "--json"],
                text=True,
                timeout=10
            )
            return json.loads(output)
        except Exception as e:
            return {"error": str(e)}

    def get_processes(self) -> list[dict]:
        """Get OpenClaw-related processes."""
        processes = []

        try:
            output = subprocess.check_output(
                ["ps", "aux"],
                text=True,
                timeout=5
            )

            for line in output.splitlines()[1:]:
                if "openclaw" in line.lower() or "node" in line.lower():
                    parts = line.split(None, 10)
                    if len(parts) >= 11:
                        processes.append({
                            "pid": int(parts[1]),
                            "cpu": parts[2],
                            "memory": parts[3],
                            "command": parts[10]
                        })
        except Exception:
            pass

        return processes

    def get_gateway_status(self) -> dict:
        """Check Gateway status."""
        result = {
            "running": False,
            "port": None,
            "pid": None
        }

        # Check if gateway is listening on default port
        try:
            # Try to get gateway info from CLI
            output = subprocess.check_output(
                ["openclaw", "status"],
                text=True,
                timeout=10
            )
            result["raw_output"] = output

            # Parse for port
            if "Gateway" in output and "running" in output.lower():
                result["running"] = True

        except Exception as e:
            result["error"] = str(e)

        return result

    def get_mcp_status(self) -> dict:
        """Check MCP servers status."""
        # Placeholder - would integrate with MCP manager
        return {
            "servers": [],
            "healthy": 0,
            "unhealthy": 0
        }
