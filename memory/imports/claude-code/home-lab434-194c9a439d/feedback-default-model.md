---
name: feedback-default-model
description: 默认模型用 MiniMax-M3
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bb80d304-cccf-47c0-85db-90200f63a1d9
  modified: 2026-07-19T17:34:59.369Z
---

用户要求默认模型用 **MiniMax-M3**。

**Why:** 用户主力模型偏好，可能因为 MiniMax-M3 在其工作流（学术+工程）上表现好或性价比合适。

**How to apply:** 新会话/任务默认假设用 MiniMax-M3；若当前环境非 M3（如本会话是 glm-5.2），提示用户通过 `/model` 或 settings.json 切换。涉及模型能力判断时按 M3 的实际能力边界给结论，不套用 Claude 系列假设。
