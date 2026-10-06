---
name: feedback-auto-git-sync
description: 用户偏好：每个任务/子任务完成后自动 git commit + push 到 GitHub，不要等用户提醒
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0763b159-87a1-4db6-b891-029e03e3b0cc
---

**Why:** 用户希望"自己跑、自动看需求去同步更新"——减少手动操作，让 GitHub 实时反映进度。

**How to apply:**
- 每完成一个实质性任务（功能、修复、数据导入、新文件、配置）→ 自动 `git add . && git commit -m "描述" && git push`
- 每次提交前确保 `.gitignore` 已覆盖敏感文件（.env、venv、日志）
- commit 信息用中文，格式简洁：`<动作>: <要点>`（例：`feat: 加 wiki OKC 解析器`、`fix: 修复 T11 reason 类型`）
- 不要 commit 临时文件、debug 打印、未保存的草稿
- 如果工作树不干净（用户中途编辑过），先 `git status` 看清楚再决定
- 关联仓库：https://github.com/Xplore-LAB/pkmemory-agent（private）

链接 [[user-current-projects]]、[[project-pkmemory-asu-paper]]