---
name: openclaw-ds-free-web
description: OpenClaw primary 改为网页 DeepSeek，local-dsv4 当首 fallback
metadata: 
  node_type: memory
  type: project
  originSessionId: eddbe800-d9d0-49fb-b7a5-f375e363fc25
  modified: 2026-08-31T00:53:26.064Z
---

OpenClaw primary 改用网页 DeepSeek（free）+ local-dsv4 兜底。

**Why:** 用户希望 OpenClaw 跟 Claude Code 一样，主交互走网页 DeepSeek 省 API 费，工具调用走本地。与 Claude Code 不同的是 OpenClaw 用 OpenAI Chat Completions 协议，不能用 CCR-aware-router；改用 OpenClaw 自身的 fallback 链。

**How to apply:**
- openclaw.json: 新增 provider `deepseek-free-web` → `http://127.0.0.1:8002/v1` (OpenAI 协议), models=[deepseek-default, deepseek-reasoner]
- openclaw.json: agents.defaults.model.primary = `deepseek-free-web/deepseek-default`
- openclaw.json: fallbacks 首位 = `local-dsv4/DeepSeek-V4-Flash-Spark-Mini-Q2-REAP-ds4.gguf`
- secrets.json: 必须加 `/models/providers/deepseek-free-web/apiKey = "no-auth-needed"`，否则 gateway 启动报 `SecretRefResolutionError`
- ds-free-api 当前上游受限流（chat 返回空），所以实际聊天走 OpenClaw fallback → local-dsv4；watchdog 恢复后才有网页 DeepSeek 实际响应

**端口选择:** :8000 必须留给 vLLM (`local-qwen` provider → vLLM :8000)，ds-free-api 走 :8002。CCR SQLite 里的 `provider-local-qwen` 也保持 :8000（`~/.claude-code-router/config.sqlite` → app_config.value_json.Providers[0].api_base_url）。

**重启流程:** 改完 openclaw.json 必须 `systemctl --user restart openclaw-gateway`，新配置才生效。**漏改 secrets.json 会导致 gateway 启动失败** (restart 循环)，补 secrets.json 后 `reset-failed` + `restart` 即可恢复。

**备份:** `/home/lab434/.openclaw/backups/openclaw.pre-ds-free-web.1788111609.json` + `secrets.pre-ds-free-web.1788111802.json` + `openclaw.pre-port-fix.1788137561.json` (端口 :8000 → :8002)

**背景:** [[ccr-aware-router]] [[deepseek-free-api]]