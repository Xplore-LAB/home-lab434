---
name: claudecode-permission-pref
description: "User's preferred Claude Code permission mode - acceptEdits + Bash whitelist, global scope"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ae1975de-33fd-4be0-af6d-ac1a40fa2a16
---

User prefers Claude Code configured with `defaultMode: acceptEdits` (auto-accept file edits) plus a **whitelist of common Bash commands** rather than a full `bypassPermissions` (`--yolo`/`--dangerously-skip-permissions`) mode. Scope: **global** (`~/.claude/settings.json`), not project-level.

**Why:** They want minimal confirmation prompts to keep flow uninterrupted, but still want a safety net against truly dangerous commands (`rm -rf /`, `git push --force` on protected branches, raw disk writes, etc.). This is a "soft bypass" — convenience with guardrails.

**How to apply:**
- When asked to "免确认模式 / no confirmation mode / 不弹窗", default to `acceptEdits` + Bash allowlist instead of full bypassPermissions.
- The current setup lives at `~/.claude/settings.json` with ~110 allow rules and ~11 deny rules. Reuse this template when configuring other machines or fresh installs.
- If they later ask for "完全跳过" or similar, escalate to `--dangerously-skip-permissions` as a launch flag rather than editing settings to bypassPermissions (keeps the safety net persistent).
- Confirmed 2026-07-14.
