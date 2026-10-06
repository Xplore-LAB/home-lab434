---
name: ccr-aware-router
description: aiohttp 内容感知代理蹲在 :3459，CCR 前置做 chat/tool 分流
metadata: 
  node_type: memory
  type: project
  originSessionId: eddbe800-d9d0-49fb-b7a5-f375e363fc25
  modified: 2026-08-30T17:04:38.375Z
---

CCR-aware-router: 蹲在 CCR (:3456) 前置的 aiohttp 代理 :3459，按请求 body 内容分发。

**Why:** CCR Router 只按 `model` 字段路由，看不到 body。用户希望「和我们对话用网页 DeepSeek，工具调用用本地 MiniMax-M3」，CCR 原生做不到。

**How to apply:**
- 路径: `/home/lab434/infra/ccr-aware-router/router.py` (aiohttp + aiohttp.ClientSession, 单 session 复用)
- systemd: `~/.config/systemd/user/ccr-aware-router.service` (After=ccr.service, 已 enable)
- Claude Code: `~/.claude/settings.json` 三处 URL `:3456 → :3459` (ANTHROPIC_BASE_URL / ANTHROPIC_API_BASE_URL / CLAUDE_AGENT_API_BASE_URL)
- 规则: messages 含 tool_use/tool_result → model="MiniMax-M3" (本地)；否则 → "deepseek-free-chat" (网页)。RESPECT_PREFIXES = deepseek-free- / deepseek- / claude- / gpt- / gemini- / /models/ (显式不改)
- 日志: `/home/lab434/infra/ccr-aware-router/logs/router.log`
- 健康检查: `curl 127.0.0.1:3459/healthz`
- 端口选择: `:3456/:3457/:3458` 全被 CCR 自身占 (gateway-bootstrap 多个端口)，必须用 `:3459+`

**端口冲突历史:** 启动时先撞 :3457 (CCR Codex gateway)，改 :3458 后又撞 CCR app-gateway，最终落到 :3459。

**背景:** [[deepseek-free-api]] [[claudecode-router-fallback]]