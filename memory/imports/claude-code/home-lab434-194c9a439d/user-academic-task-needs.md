---
name: user-academic-task-needs
description: 用户希望我协助的四类学术任务：文献调研/综述、论文写作、数据集与实验设计、代码工程实现
metadata: 
  node_type: memory
  type: project
  originSessionId: 0763b159-87a1-4db6-b891-029e03e3b0cc
---

用户希望长期、持续地获得以下四类学术辅助：

1. **文献调研 / 综述**
   - 查最新论文（arXiv、IEEE Xplore、CNKI、万方、DBLP、Google Scholar）
   - 整理 references、做阅读笔记、对比方法

2. **论文写作辅助**
   - 写/改段落、整理大纲、降重、润色（中英文双语）
   - 配图描述、表格设计、response letter 起草

3. **数据集与实验设计**
   - 设计 SFT 数据集（指令对、思维链）
   - 构造 benchmark 题（与 `test_20q.py` 风格一致）
   - 规划消融实验

4. **代码 / 工程实现**
   - 训练 pipeline（与 `CAC2026_ASU_OKC_SFT/04_*` 对齐）
   - benchmark 脚本（与 `bench/bench_ds.py` 对齐）
   - 推理服务、KG 构建脚本

**Why:** 用户原话「做点学术研究」「希望你自己有个大的记忆，记住我关于学术方面的点点滴滴」——表明这是一个长期的、跨多个工作面（写作/代码/数据）的助手关系。

**How to apply:**
- 接到学术任务时，先问"这是哪个项目/哪一类任务"，避免跑偏
- 长期跟踪用户研究方向演进（论文投稿进展、新方法、新数据集），跨对话保持上下文
- 链接 [[user-research-directions]]、[[user-current-projects]]、[[user-writing-language]]