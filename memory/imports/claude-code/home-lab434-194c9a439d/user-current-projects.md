---
name: user-current-projects
description: 用户当前进行的四个主要研究项目：空分 ASU、CAC2026 OKC-SFT、LLM benchmark、新立项的 pkmemory-agent
metadata:
  node_type: memory
  type: project
  originSessionId: 0763b159-87a1-4db6-b891-029e03e3b0cc
---

用户当前有四个并行进行的项目：

### 1. `air-separation-project/`（空分装置研究主线 · 老主线）
- 路径：`/home/lab434/air-separation-project/`
- 含版本：`v2`、`v3`、`v4`、`v5`（v5 最新，含 STATUS_2026-06-24.md）
- 子目录：`distill/`、`logs/`、`outputs/`、`wiki/`
- 关键问题域：**氮塞（nitrogen plugging）**——低温空分中的常见异常工况
- 含 `test_20q.py`（20 题评测脚本）+ `test_20q_nitrogen_plugging.jsonl`（评测集）
- wiki 内含 **10 异常场景 × 6 任务类型 = 60 OKC 样本**（已用于 pkmemory-agent 入库）

### 2. `CAC2026_ASU_OKC_SFT/`（**已投出** · 等审稿）
- 路径：`/home/lab434/CAC2026_ASU_OKC_SFT/`
- 论文主题：**Operation Knowledge Chain Supervised Fine-Tuning for Abnormal Operation Handling**
- 投 **CAC2026**（中国自动化大会 2026）· **2026-07 已投出**，等审稿结果
- 关键概念：**OKC（Operation Knowledge Chain）**——把异常工况处理流程拆成操作知识链用于 SFT
- 与 pkmemory-agent 关系：pkmemory-agent 是其理论升级版（OKC 扩展为完整 9 字段记忆体系）

### 3. `bench/`（LLM benchmark · 相对独立）
- 路径：`/home/lab434/bench/`
- 测试对象：DeepSeek V4 Q2 量化版在 GB10 上的推理性能
- 输出：`bench_results.json`、`dsv4_benchmark.pdf/xlsx`、多张 sheet PNG
- 关注指标：prompt_tps、gen_tps、ttft、wall_ms

### 4. `pkmemory-agent/`（**新主线，2026-07 启动**）
- 路径：`/home/lab434/air-separation-project/pkmemory-agent/`
- 论文主题：**面向空分运行监盘的工业智能体过程知识记忆构建方法**
- 英文：**A Process Knowledge Memory Construction Method for Industrial Agents in Air Separation Operation Monitoring**
- 状态：MVP 完整，GitHub 私有仓同步
- 核心实现：
  - 9 字段 Pydantic MemoryUnit + 5 类记忆（state/procedure/case/safety/mechanism）
  - Neo4j 5.x 存储 + 原生向量索引 + RRF 三路混合检索
  - LangGraph 5 节点 agent（understand→retrieve→reason→safety→format）
  - VLLM (Qwen3.6-35B-A3B-NVFP4) + BGE-M3 Embedding
  - Web UI（FastAPI 8088，含实时监盘 + 自动决策）
  - DCS 模拟器（14 变量 + 4 异常模式）
  - 后台 daemon（HTTP 驱动，自动报警→决策）
- 评测：
  - 20 题 benchmark vs baseline：完整管线 4.95/5 字段（基线 0.20/5）
  - 7 变体消融 + LLM-as-judge：检索贡献最大，understand 节点可消融
- 论文素材：
  - `paper-draft/ch05_pkmemory_construction.md`（第 5 章 319 行）
  - `paper-figures/` 11 张配图（含 8 张原 + 3 张 live）
- 关系：**是 CAC2026 OKC-SFT 的理论升级版**——OKC 扩展为完整记忆体系
- 仓库：https://github.com/Xplore-LAB/pkmemory-agent（private，已 10+ commit）

**Why:** 这些是用户当前最活跃的工作面。pkmemory-agent 是新启动的主线（2026-07），地位已超过原来的 CAC2026 投稿。

**How to apply:**
- 学术写作/综述任务：默认围绕 pkmemory-agent + ASU 异常工况展开
- 代码任务：先看 `pkmemory-agent/` 是否已有可复用组件
- benchmark 任务：参考 `bench/bench_ds.py` 和 `pkmemory-agent/eval/bench.py` 两种范式
- 链接 [[user-research-directions]]、[[user-research-infrastructure]]、[[project-pkmemory-asu-paper]]