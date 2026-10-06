---
name: feedback-fast-reuse-strategy
description: 用户学术研究策略：极速、复用优先、多用开源基础和别人的已有工作，只增量自己的 idea
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0763b159-87a1-4db6-b891-029e03e3b0cc
---

**Why:** 用户原话（2026-07-15）："越快越好，所以要有计划有安排，多复用别人的基础经验知识能力，再加上我们自己的idea就好了。"

**核心模式：**
1. **不开新坑**——已有模型/数据集/框架/评测直接用，不重写
2. **复用为骨，idea 为肉**——把别人的成熟工作当骨架，我们只插入自己的 idea（过程知识链 / 9 字段 / 一致性筛选 / 实时监盘）
3. **少写代码多写论文**——能引用的代码用 git submodule，能引用图表就截图引用

**How to apply:**
- 选 venue 优先会议（4-8 页）而不是期刊（10-15 页）
- baseline 直接用 vanilla RAG / AutoGen / 标准 LangGraph，不重新发明
- benchmark 用现成公开的（MMLU subset / HotpotQA / 2WikiMultiHopQA），不必自己造题
- baseline 数据集用现有 KG（Wikidata / ConceptNet）做对照，不重复爬
- 写论文时把工程细节当 Implementation Notes，不当 Contribution
- 聚焦贡献 = 3 条（统一记忆表示 / 过程链构建 / 一致性筛选与调用）
- 时间分配：代码 20% / 论文写作 60% / 调研 20%

**关联：** [[user-current-projects]]、[[project-pkmemory-asu-paper]]