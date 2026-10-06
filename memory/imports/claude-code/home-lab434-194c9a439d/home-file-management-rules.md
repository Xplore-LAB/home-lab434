---
name: home-file-management-rules
description: /home/lab434 长期文件管理规则（10 分类体系 + canonical path + KEEP_IN_PLACE 原则 + safe delete + Git 规则 + 新项目规则）。所有 Agent 操作 /home/lab434 前必读。
metadata:
  type: feedback
  originSessionId: home-reorg-2026-08-19
  modified: 2026-08-19T03:25:16.819Z
---

# /home/lab434 长期文件管理规则

**生效日期**：2026-08-19
**适用范围**：所有 Claude Code / OpenClaw Agent 操作 /home/lab434 时

---

## 1. 唯一事实源（Single Source of Truth）

`/home/lab434/workspace/README.md` 是项目 canonical path 的唯一事实源。

- **操作任何已有项目之前，必须先读这个文件**，确认 canonical path
- **禁止看到同名目录后自行选择一个修改**
- **禁止把几十个当前项目的绝对路径全部写进 Memory**——具体路径、项目状态和新增项目统一维护在 workspace/README.md

---

## 2. 10 分类体系

以后新产生的内容统一按以下 10 类判断：

| 类别 | 含义 |
|---|---|
| **Research** | 长期科研主线 |
| **Papers** | 具体论文、投稿及论文材料 |
| **Projects** | 可独立运行/部署/开源的自研项目 |
| **Models** | 模型权重、Adapter、Checkpoint |
| **Datasets** | 原始数据、训练集、测试集、Benchmark 数据 |
| **Experiments** | 训练、消融、复现、Benchmark、运行结果 |
| **Infrastructure** | Docker、服务、环境、部署、监控、脚本 |
| **ThirdParty** | 第三方仓库、框架、Fork |
| **Knowledge** | 文献、笔记、教程、Wiki、参考资料 |
| **Archive** | 历史版本、旧项目、备份、trash-review |

**推荐结构**（已有项目**不强制迁移**）：

```
/home/lab434/workspace/
├── research/
├── papers/
├── projects/
├── experiments/
└── README.md
models/
datasets/
infra/
third_party/
knowledge/
archive/
```

---

## 3. 一个项目一个主分类 + 一个 Canonical Path

- 一个项目只能有一个主要可信位置
- 项目可能同时涉及论文、数据、实验，但只指定一个主身份
- 论文、数据、实验通过 README 建立关联，不复制多个项目副本
- 例如：PKMemory 主分类 = Research/ASU/PKMemory

---

## 4. 禁止擅自物理整理（KEEP_IN_PLACE 原则）

未经用户明确要求，不得因为"目录更整齐"而：
- mv 大型项目
- 移动 Python venv
- 移动模型目录
- 改变 systemd / Docker / Caddy 使用路径
- 移动 .openclaw 工作区
- 重构正在运行的服务目录

**已有 HIGH / CRITICAL 路径默认：KEEP_IN_PLACE**

包括但不限于：
- systemd 硬编码目录（22+ 个 unit）
- Docker compose 硬编码目录（4 个）
- Caddyfile 硬编码目录
- 9 个 Python venv
- 357G 模型目录 + 40G models-local-qwen38
- 所有 ASU 主线
- .openclaw/workspace/（含秋招/公众号隐私）

---

## 5. 删除规则（Safe Delete Policy）

任何不确定文件默认：**KEEP**——不能直接 rm。

低风险待删除内容优先移动至：
```
/home/lab434/archive/trash-review/YYYY-MM-DD/
```

**以下内容禁止未经确认删除**：
- 模型权重
- checkpoint / adapter
- 原始数据
- 实验关键结果
- 论文源文件
- 专家数据
- 未提交 Git 修改
- 未 push Git 仓库
- Docker / systemd 配置
- OpenClaw 数据
- 唯一备份

**大文件疑似重复时先比较**：
- 路径
- 大小
- inode
- 模型配置（GGUF metadata / safetensors header）
- 必要时 SHA256 全量哈希

确认后再处理。

---

## 6. Git 规则

修改代码前先执行：
```bash
git status
git branch --show-current
git remote -v
```

**不得**为了 git clean 而随意：
- `git add .`
- `git reset --hard`
- 删除 untracked 大范围
- 大范围修改 .gitignore

**源码、论文源文件和不可重建关键结果**优先进入版本控制。

**cache、venv、log、明确可重建文件**才进入 .gitignore。

**Git dirty 状态必须先检查和分类**——92+ dirty 文件需要分组成可执行 commit，而不是一次性 commit。

---

## 7. 新项目规则

以后创建新内容前先判断属于哪一类：

| 内容类型 | 归属 |
|---|---|
| 研究问题 | | `workspace/research/` |
| 论文投稿 | | `workspace/papers/` |
| 独立软件项目 | | `workspace/projects/` |
| 单次实验 | | `workspace/experiments/` |
| 模型 | | `models/` |
| 数据集 | | `datasets/` |
| 服务 / 部署 | | `infra/` |
| 第三方 clone | | `third_party/` |
| 资料 / 文献 | | `knowledge/` |
| 历史内容 | | `archive/` |

**禁止再次直接在 /home/lab434/ 根目录随意创建新的大型项目**。

---

## 8. workspace/README.md 维护规则

- 把 `/home/lab434/workspace/README.md` 作为服务器项目的唯一总索引
- 每个重要项目至少记录：
  - 项目名称
  - 类别
  - canonical path
  - 状态
  - Git remote
  - 主要数据
  - 实验位置
  - 论文位置
  - 服务依赖
  - 备注

- 状态统一使用：
  - **ACTIVE**
  - **CANONICAL**
  - **SUBMITTED**
  - **FROZEN**
  - **LEGACY**
  - **ARCHIVED**
  - **THIRD_PARTY**
  - **KEEP_IN_PLACE**

- 当项目路径发生变化时：**优先更新 README**，而不是把新路径长期写死在 Memory

---

## 9. 设计目标

目录结构的目标是 **"可定位、可维护、唯一可信"**，而不是追求根目录视觉整洁。

---

## 10. Python venv 规则

**Python venv 不直接移动**——只记录并 Python 重建。

---

## 11. 模型权重规则

**模型权重不因目录整理而复制或删除**——只查重复和依赖。

---

## 12. trash 规则

**trash 优先进入 `archive/trash-review/`，不得直接永久删除**——保留 30 天观察期后由用户决定 rm -rf。

---

**Why:** 这是 2026-08-19 FAST CLOSE 完成后确立的服务器级治理规则，防止不同 Agent 后续随意创建目录、重复项目或误删文件。

**How to apply:**
- 任何 Agent 进入 /home/lab434 后第一件事：读 `~/workspace/README.md`
- 创建新项目前：先看属于哪一类，按 7 规则放置
- 删除任何文件前：按 5 规则判断
- 移动现有项目：默认 KEEP_IN_PLACE，除非用户明确要求
- 修改代码前：按 6 规则检查 Git 状态