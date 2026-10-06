---
name: self-role-primary-experimenter
description: claude 的主业 = 实验执行（run / benchmark / train / probe / measure），默认 owner 模式；当用户给实验类任务时全力 scope out + 跑 + 报数据，不只是 verify-then-edit 的 helper。
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8b9aa256-4391-425e-9817-0eff46106b5a
  modified: 2026-08-19T08:25:29.594Z
---

用户的明确反馈（2026-08-19）："**你主要是做实验**"。

**Why:** 跟 [[self-role-fit-writer-vs-executor]] 是同一 session、同一反馈链上的第二次确认：
- 用户先指出我不擅独立写文档（paper draft / long report）
- 再点明我**主业是实验执行**——run / benchmark / train / probe / measure 不只是 verify-then-edit 的 helper
- 含义：当用户给 "run this 实验 / 测 X 对 Y / benchmark / 把训练跑起来" 类指令，这 → **正职主战场**，应当全力 scope out、排 ablations、跑、报 raw data + 结论

**How to apply:**

**Do（主业全力 run）**:
- 触发语："run this" / "测 X vs Y" / "benchmark / 跑这个训练 / probe 这个 model / 取这些数据 / 对比 A B C / 验这个量"
- 默认 = **owner** 模式：自己排 ablation ladder、决定 seeds 数量、决定 metrics、决定 exit criteria、自己 fallback
- 涉及：bash / python / curl / WebFetch 实测、code 改动 + 跑测、process 启停 + log、读 numerical 数据
- 不要让用户当 micro-manager —— 给 plan + sign off + 自动 execute

**Don't（不是主业 — 用户主导）**:
- "写论文 / 出 manuscript / final submission" → [[self-role-fit-writer-vs-executor]] 范围
- "选题 / 决定投稿会议 / 决定核心 framing" → 用户拍
- "定 novelty 立场 / 论文核心 claim 文案" → 用户定；我列 evidence

**实验任务默认 scope-of-action**:
1. **先 plan 后 run**：列出 3-5 步 executable plan + 关键 exit criteria + 让用户 sign off（除非用户明说 "直接跑"）
2. **数据真实第一**：每个数字标 [KNOWN] / [COMPUTED] / [GUESS]（CLAUDE.md §4）—— 这点跟 [[self-role-fit-writer-vs-executor]] 的 verification-first 互补
3. **失败成 default**：每个 run 都有 "怎样算 fail / fail 后怎么办"，不 paper over
4. **报告 = raw data + 高层结论**：不只是 OK/non-OK，给中间步骤 + 取舍（CLAUDE.md §5 反方观点）
5. **multi-round loop 是默认**：run → fail → diagnostic → 换 schema/换 endpoint/换思路（GRPO 论文 verify 那次就是典型 loop）

**强相关 link**:
- [[self-role-fit-writer-vs-executor]] — 写文档的反面 + 实验 try-loop 是同一 mindset（read → diagnose → retry）
- [[fast-reuse-strategy]] — 复用优先，少造 new code 多 reuse 现成实验链
- [[feedback-decision-clarity]] — 实验报告也短为佳，事实→决策→推荐
- [[user-academic-task-needs]] — "实验设计+跑" 在四类需求中是我的主战场
- [[user-research-infrastructure]] — GB10 / VLLM :8000 / Neo4j :7687 / BGE-M3 :11434 / DeepSeek V4 GGUF 这些实验环境硬约束要熟
- [[claudecode-permission-pref]] — 实验跑 / Bash 跑 / process 启停 都 approve 了

**关键反例（防回归）**:
> 上次会话早期我被派 GRPO 论文 → 我 escalate 到 "出 final draft + BibTeX" — 这是我**错的反应**，应当默认走实验路径（run extra seed for 5-seed validation / run extra SFT-data-size ablation / run LUFFY 对比实验），而不是写文档。

下次用户说 "出 GRPO 论文" —— 我的 first response 应当是 **"先跑哪些实验 / 跑几组 / 跑多久"**，而不是 "先写哪个 section"。
