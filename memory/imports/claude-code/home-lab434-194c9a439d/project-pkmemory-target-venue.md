---
name: project-pkmemory-target-venue
description: pkmemory-agent 论文目标：AI 顶会（NeurIPS / ICML / ICLR / AAAI / ACL / EMNLP / CVPR 等）。这是硬性目标，所有技术决策和写作标准都要按顶会门槛对齐
metadata: 
  node_type: memory
  type: project
  originSessionId: 0763b159-87a1-4db6-b891-029e03e3b0cc
---

**目标 venue：AI 顶会**
- 主目标：**NeurIPS / ICML / ICLR**
- 次目标：**AAAI / IJCAI / ACL / EMNLP**（自然语言/Agent方向）
- 备选：**CVPR**（如果走多模态）/ **AAMAS / IROS**（Agent + Robotics）
- 还可以考虑：**Workshop 形式**（NeurIPS Workshop on RAG / Agents / Knowledge）—— 容易一些，2-3 个月可冲

**顶会 vs 中文期刊/会议的关键差距（必须补的）：**

| 维度 | 当前（中文期刊级） | 顶会要求 | 需补 |
|---|---|---|---|
| **Novelty** | 9字段 + 5类记忆 + 过程链 | 必须有理论 insight，不能只是 framework | 形式化证明 chain completeness / consistency bounds |
| **Baselines** | 只有"直接 prompt" | 至少 3-4 个 SOTA baseline | ReAct / MemGPT / AutoGen / Generative Agents / Vanilla RAG / KG-RAG |
| **数据集规模** | 64 个 MemoryUnit + 20 题 | 至少 5-10 倍 | 多领域 + 至少 200-500 题 |
| **通用性** | 只在 ASU | 至少 1 个新场景验证 | 抽一两个非化工领域（如医疗、金融或通用 agent 任务）证明通用 |
| **统计显著性** | 单次跑 | 多次跑 + t-test | 加随机种子 + 显著检验 |
| **理论分析** | 无 | 复杂度 / 收敛性 / 信息论 | chain length vs quality bounds / retrieval recall vs generator accuracy |
| **Human eval** | 无 | 至少小规模 | 找 2-3 个领域专家评 30-50 个样本 |
| **Reproducibility** | GitHub 私有 | 必须公开 + code release + 模型权重 | 公开仓库 + README + 安装脚本 |
| **Ethics / Broader Impact** | 无 | 必填章节 | 工业 AI 风险的简单论述 |

**时间线（按顶会准备）：**
- 现在（7 月）：MVP + 素材 ✅
- 8-9 月：补 SOTA baselines + 多领域 + 统计显著性
- 10 月：**AAMAS 2026 deadline？** 或 **NeurIPS 2026 workshop**
- 12 月：**AAAI 2027 deadline**（通常 8 月截止，已过→ 转投 NeurIPS/ICML）
- 2027 Q1：**ICLR 2027 workshop / ICML 2027 workshop**
- 2027 Q2：完整冲 ICML / NeurIPS 主会

**现实路径**（用户原话"越快越好"）：
- **最快**：3-4 个月后冲 NeurIPS workshop on RAG/Agents
- **稳妥**：6 个月冲 AAAI 2027
- **理想**：9 个月冲 NeurIPS/ICML 主会

**Why:** 这是 2026-07-15 用户明确指示的硬性目标，所有后续决策（实验设计、baseline 选择、写作风格、补充材料）都按顶会门槛做。

**How to apply:**
- 不要写"框架章节"凑数（顶会审稿人一眼看穿）
- Baseline 必须有 SOTA，不能用 trivial baselines
- 实验必须有 stat sig，不能 single-seed
- 必须有 ablation 表 + generalization 验证
- 写作风格：concise、every sentence counts、no fluff
- 长度：8 页主文 + 不限 supplementary（多放实验和案例）
- 代码必须公开

**关联：** [[user-current-projects]]、[[user-research-directions]]、[[project-pkmemory-asu-paper]]