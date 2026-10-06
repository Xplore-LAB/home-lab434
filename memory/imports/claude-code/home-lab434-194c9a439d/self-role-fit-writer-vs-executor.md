---
name: self-role-fit-writer-vs-executor
description: claude 不擅长独立产出长文档（paper draft / long report），擅长多轮执行试错（run/verify/iterate/调研）。用户让 claude 写文档时，必须先 outline + 单章节让用户检视，绝不一次 W 整篇。
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8b9aa256-4391-425e-9817-0eff46106b5a
  modified: 2026-08-19T08:22:21.453Z
---

用户的明确反馈（2026-08-19）：我**不适合直接写文档**（如 paper draft、长 markdown 报告、final BibTeX、submission-ready 文案），**擅长的是不断尝试的执行试错**（反复 run / verify / iterate / 调研 / 失败再换思路）。

**Why:** 在 2026-08-19 GRPO Cold-Start 论文工作中暴露：
- deep-research workflow 返回的 30+ 文献里，**~40% 的 arXiv ID 是错的**（2507.07403 是物理论文、2208.08267 是数学论文而非 STaR 等），subagent 自报 [KNOWN] 实为 false positive
- 我若 produce "verified 引用 + Novelty 总结 + final §2.4" 一旦进入 W 字级文案，**准确性下滑很快**——必须由用户当 gate
- 反之当用户派"试一下 / 调研 / execute task"——这正是我擅长的 loop：**单 round 失败 → diagnostic → 再 run → 换思路**（典型：curl arxiv API 第一次 grep 把 envelope fallback title 当 paper title → 立即重 parse → 命中真 entry）

**How to apply:**

**触发"写文档"任务时拒绝自主 W 整篇**：
- "出 final draft / 出 submission paper / 出 final BibTeX" → 出 **outline + 子任务清单 + 单章节 30min 草稿 + 给用户审**，用户确认后再 Edit 增量
- 绝不一次 Write > 500 字的整篇 manuscript / report
- 写文档一律 Edit 增量，绝不 Write 替换已存在文件（CLAUDE.md §3 铁律）
- 改前必 Read 完整（CLAUDE.md §3 铁律），改后必 Read 头尾核对报告行号

**触发"执行 / 试错 / 调研"任务时大胆 loop**：
- "试一下 / verify / 跑一下 / 查一下" → 大胆 multi-round（run → fail → diagnostic → 再 run → 换 schema / 换 endpoint / 换思路）
- WebSearch / WebFetch / curl / bash 多轮试出真值，不 spam 重试，按 CLAUDE.md "失败一次就 tool_describe 看 schema"

**Verification-first（贯穿两类任务）**：
- 任何"verified"事实（引用、ID、数字、统计）必须先 WebFetch / curl 真验证
- subagent 的 [KNOWN] 标签 = **不可信**，必须自己 re-verify（这次踩雷的真实案例）
- 用户让 "按推荐来" 时：默认 verify-then-edit 路径，**绝不 auto-write 整篇**

**绝对禁止的文风**：
- "I have produced the paper draft for you to submit" 这类 autonomous-publication claim
- "Final submission ready" 这类对最终交付的口头承诺
- 把 suspicious ID 列进 BibTeX 不标 [TO BE VERIFIED]

**强相关 link**：
- [[fast-reuse-strategy]]（写文档时优先复用已 verified 内容，不重造）
- [[feedback-auto-git-sync]]（每次小写完就 commit，不攒大改）
- [[home-file-management-rules]]（写新文件前想清楚归类位置）
- [[feedback-decision-clarity]]（决策时刻短，**不**用写满 1500 字当成果）
- [[claudecode-permission-pref]]（Edit 类操作本来就 bypass-permission，安全）

**关键反例（下次踩同样的坑时立刻退回这条）**：deep-research subagent 报 30 篇 ID 全是 [KNOWN]—— 我应该 confirm 6 个 sample 就足够 alert（"再 confirm 之前不要相信"），而非全盘 accept 入 §2.4。下次类似 deep-research task 第一步 = 抽 3 个 known-good ID（DeepSeekMath、STaR 这类高知名度） parse 一次确认 schema 正确，再 trust 整体。
