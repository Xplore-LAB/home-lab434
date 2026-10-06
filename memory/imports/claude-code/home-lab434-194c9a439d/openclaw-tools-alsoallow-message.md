---
name: openclaw-tools-alsoallow-message
description: openclaw tools.alsoAllow 的 message/group:messaging 不能删，weixin channel 依赖
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d2e21f4d-0f1f-411f-8eb1-a03c295ba075
  modified: 2026-07-18T16:28:59.298Z
---

openclaw `tools.alsoAllow` 里的 `"message"` 和 `"group:messaging"` **不能删**，即使 doctor 报 "unknown entries"。

**Why**: 2026-07-19 清理 allowlist 时误删这俩，doctor 立刻报 "Agent main routed from openclaw-weixin, but message tool unavailable; sendAttachment/upload-file/thread-reply/reply can fail"。doctor 的 "unknown entries" 是因为当前 runtime 未加载该工具，但 weixin channel 运行时需要 —— 删了会断微信收发附件/回复功能。

**How to apply**: 看到 `tools.* allowlist contains unknown entries (message, group:messaging)` 警告时，**保留不动**。这是 doctor 误报，删了反而出事。related [[openclaw-config-health]]
