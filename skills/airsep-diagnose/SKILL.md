---
name: airsep-diagnose
description: "空分装置（air separation unit）工况诊断与节能分析。当用户提供 DCS 截图 / 现场照片 / 时序数据（CSV 或表格），或提到 氧纯度、导叶开度、下塔液空、膨胀机、异常工况、工况漂移、能耗优化、节能空间、过量控制 时激活。可读出截图中的工艺参数，写入时序记忆，并给出趋势 / 异常 / 因果分析。"
user-invocable: true
---

# AirSep Diagnose — 空分装置工况诊断

把 **DCS 截图 / 时序数据** 变成 **可查询的因果记忆**，再回答「**发生了什么、为什么、能省多少**」。

## 何时用

- 用户发来 DCS 截图 / 现场仪表照片 → 读出工艺参数
- 用户提到「氧纯度掉了」「导叶开度」「能耗」「节能空间」→ 做趋势 / 因果分析
- 用户给 CSV / 表格时序数据 → 存记忆 + 分析

**不适用**：与空分/工业过程无关的通用问答；单纯图片美化。

## 能力链（4 步）

```
① 读图      dcs_read.py   → StepFun 视觉读出 (时间, 指标, 值, 控制量)
② 记忆      memory_io.py  → 写入 asmemory（状态事件 + 动作事件）
③ 分析      diagnose.py   → 趋势 / 异常 / 因果（纯时序数学，不靠 LLM 猜）
④ 报告      diagnose.py   → 结构化报告 + 节能空间估计
```

## 命令调用规范

所有命令从 skill 目录运行：

```bash
cd <skill_dir>

# ① 读图：DCS 截图 → 结构化 JSON
bash run.sh read --image /path/to/dcs.png --out /tmp/dcs_read.json

# ② 存记忆：把读出的数据写入 asmemory
bash run.sh store --in /tmp/dcs_read.json

# ③ 分析：趋势 + 异常 + 因果
bash run.sh analyze --metric oxygen.purity --action valve_adjust

# ④ 一次性端到端
bash run.sh full --image /path/to/dcs.png
```

## 输出约定

- **`read`** 输出 JSON：`{"readings":[{"ts":..., "entity":"oxygen", "metric":"purity", "value":99.2, "unit":"%"}, ...], "actions":[{"actor":"operator","verb":"valve_adjust","object":"guide_vane","amount":68.0}], "confidence":...}`
- **`analyze`** 输出人读报告；最后一行形如 `MEDIA:/abs/path/report.png` 时，Agent 会渲染为图片（rich-output 协议）

## 依赖

- `python3` ≥ 3.10（零第三方依赖）
- StepFun API Key：`$STEPFUN_API_KEY`（或读 `~/.openclaw/secrets/stepfun.key`）
- asmemory：`$ASMEMORY_HOME`（默认 `~/.asmemory/`）

## 失败处理

| 现象 | 原因 | 处理 |
|---|---|---|
| `read` 返回空 `readings` | StepFun 是推理模型，思考吃光了 token | 脚本已设 `max_tokens≥2048`；若仍空，提高 `MAX_TOKENS` |
| `analyze` 报「样本不足」 | 记忆库中该指标点太少 | 先 `store` 更多数据，或降低 `--min-points` |
| `401` | API Key 缺失/过期 | 检查 `~/.openclaw/secrets/stepfun.key` |
