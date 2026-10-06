---
name: user-research-directions
description: 用户的三个核心研究方向：工业过程控制+AI/LLM、大模型微调与评测、知识图谱/Neo4j
metadata: 
  node_type: memory
  type: project
  originSessionId: 0763b159-87a1-4db6-b891-029e03e3b0cc
---

用户的三个交叉研究方向：

1. **工业过程控制 + AI/LLM**
   - 具体应用场景：空分装置（Air Separation Unit, ASU）的异常工况处理
   - 把大模型用于操作知识问答、决策辅助

2. **大模型微调与评测**
   - 关注 SFT（Supervised Fine-Tuning）、知识蒸馏（Distillation）、量化（Quantization）
   - 关心模型能力 vs. 部署效率的权衡
   - 在 Blackwell GB10 等边缘/工作站级硬件上做本地推理评测

3. **知识图谱 / Neo4j**
   - 用于领域知识（过程工业）建模与问答
   - 本地已运行 Neo4j 服务（Java 进程占 ~3 GiB 内存）

**Why:** 这三条线在用户的项目里实际是耦合的——空分项目同时涉及领域 KG + LLM SFT + benchmark。

**How to apply:**
- 推荐方法时优先考虑三个方向都能复用的方案
- 涉及具体技术选型时给出「在工业场景 + 本地 GB10 + 量化模型」约束下的可行性判断
- 链接相关记忆 [[user-research-infrastructure]]、[[user-current-projects]]