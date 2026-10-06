# Agent Toolkit

> 常见 Agent 问题的一站式解决方案套件

## 包含模块

### 1. Workspace Governance（工作区治理）
- `scaffold/` - 项目脚手架模板
- `new` - 快速创建脚本
- `FILE-MAP.md` - 目录规范
- `BEST_PRACTICES.md` - 文件操作最佳实践

### 2. Experiment Runner（实验运行器）
- `run_experiments.py` - MiMo-V2.6-RL-oss 实验工具
- `batch_experiments.sh` - 批量实验脚本
- `EXPERIMENT_SOP.md` - 实验标准流程

### 3. Research Notes（研究笔记）
- `research/` - 调研文档和笔记
- `memory/` - 经验沉淀

### 4. Utils（工具集）
- `utils/` - 通用工具函数
- `hooks/` - 策略钩子
- `templates/` - 可复用模板

## 快速开始

\`\`\`bash
# 1. 创建新项目
new project my-project

# 2. 运行实验
python3 run_experiments.py smoke-test --instance <IID>

# 3. 批量实验
bash batch_experiments.sh
\`\`\`

## 设计原则

1. **可插拔 vs 需要沉淀** - 区分会过时的外在和会沉淀的内在
2. **Workspace as Source of Truth** - 文件系统是持久状态
3. **Safety by Design** - 路径白名单、沙箱隔离、fail-fast
4. **Human-in-the-Loop** - Agent 提案，人类决策
