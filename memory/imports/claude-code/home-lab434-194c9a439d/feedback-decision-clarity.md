---
name: feedback-decision-clarity
description: "When asking the user to make a decision, keep it minimal — facts → decision point(s) → recommendation. Avoid stacking tables, anti-patterns, failure-mode lists around the decision."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3ef468df-c3bf-4ac8-b790-fb3714c9c576
---

When a reply ends with "what should we do next?", keep the decision portion minimal:

**Pattern**:
1. State current facts (1-2 lines max).
2. State the decision point(s) — ideally one, never more than three.
3. State your recommendation (per CLAUDE.md "不甩锅：能自主判断的自己拍").
4. Stop.

**What NOT to do** (this is what triggered the feedback on 2026-07-15):
- Tables of status with multiple columns when the user just needs to know "done / not done / blocked"
- Stacking "反方 / 证据 / 失败模式" anti-patterns around a simple yes/no
- Listing 3 follow-up options with descriptions when 1 with a recommendation suffices
- Repeating the same state from earlier in the conversation

**Why**: User said "好复杂，让我做决策的时候，你的逻辑要清晰点". They want **decision-making friction low**, not exhaustive analysis. The CLAUDE.md §5 "对抗式审查" is for deliverable review, not for asking the user what to do next.

**How to apply**:
- Anti-patterns and failure modes belong in the *deliverable review* (CLAUDE.md §5), not around decision prompts.
- When the user has to choose, give: facts → choice → your pick. Full stop.
- If a follow-up list is genuinely needed (e.g., 3 unrelated tracks), mark which you recommend with "(Recommended)" and put it first.

Related: [[feedback-fast-reuse-strategy]] (similar spirit: avoid ceremony around the work itself).