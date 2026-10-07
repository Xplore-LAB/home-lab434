# Plan Directory Skill

在创建任何新目录、项目或文件前，必须先调用此 skill 检查路径规划规则。

## 触发条件

当出现以下情况时，自动激活此 skill：
- 需要创建新目录
- 需要创建新项目
- 需要移动/重命名目录
- 用户要求创建文件、项目、实验等

## 执行流程

### 1. 读取规则文件

```bash
cat ~/.config/dir-planning/rules.yaml
```

### 2. 检查现有结构

```bash
ls -la ~/src/
ls -la ~/data/
ls -la ~/apps/
ls -la ~/Documents/
```

### 3. 规划路径

根据内容类型，选择合适的目录：
- **代码项目** → `~/src/<project-name>/`
- **数据集** → `~/data/datasets/<dataset-name>/`
- **模型权重** → `~/data/models/<model-name>/`
- **脚本工具** → `~/scripts/<tool-name>/`
- **文档笔记** → `~/Documents/<topic>/`
- **服务部署** → `~/apps/<service-name>/`
- **实验产出** → `~/data/experiments/<experiment-name>/`

### 4. 确认创建

如果路径不明确，向用户确认：
```
建议将 <项目名> 创建在 ~/src/<项目名>/
是否继续？
```

### 5. 执行创建

创建目录后，立即初始化项目结构（如 README.md、.gitignore 等）。

## 目录结构规范

```
~/
├── src/                # 代码项目（替代 projects/）
│   ├── <project-name>/
│   ├── research/       # 研究项目
│   └── experiments/    # 实验原型
│
├── data/               # 数据资产
│   ├── datasets/       # 公开/私有数据集
│   ├── models/         # 预训练模型权重
│   ├── raw/            # 原始数据
│   ├── processed/      # 处理后数据
│   └── experiments/    # 实验产出
│
├── apps/               # 自部署服务
│   ├── <service-name>/
│   └── deploy/         # 部署配置
│
├── backups/            # 备份归档
├── docs/               # 项目文档
├── Documents/          # 个人文档、笔记
├── logs/               # 日志
└── scripts/            # 脚本工具
```

## 命名规范

- 全小写 + 连字符：`my-project` 而非 `my_project` 或 `MyProject`
- 避免中文目录名（跨机器/跨脚本容易出编码问题）
- 避免空格和特殊字符
- 简洁明了：`qwen-ab-test` 而非 `qwen_ab_test_v2_final`

## 强制检查清单

在创建任何新目录前，必须回答：
- [ ] 是否已读取 ~/.config/dir-planning/rules.yaml？
- [ ] 是否已检查现有目录结构？
- [ ] 是否选择了最合适的目录？
- [ ] 是否遵循命名规范？

如果以上任何一项为"否"，必须先完成再继续。

## 示例

**场景 1：用户要求创建一个新的深度学习项目**
```
用户：帮我创建一个新的图像分类项目
Agent：
1. 读取 rules.yaml
2. 检查 ~/src/ 现有结构
3. 建议：~/src/image-classification/
4. 确认后创建
```

**场景 2：用户要求下载数据集**
```
用户：下载 CIFAR-10 数据集
Agent：
1. 读取 rules.yaml
2. 检查 ~/data/datasets/
3. 建议：~/data/datasets/cifar-10/
4. 确认后下载到该目录
```

**场景 3：用户要求创建脚本**
```
用户：写一个备份脚本
Agent：
1. 读取 rules.yaml
2. 检查 ~/scripts/
3. 建议：~/scripts/backup.sh
4. 确认后创建
```

## GitHub 仓库自动化

对于重要的项目，自动创建对应的 GitHub 仓库：

### 触发条件
- 创建新的代码项目（在 ~/src/ 下）
- 项目包含 README.md
- 用户明确要求或项目重要性较高

### 执行流程
1. 检查项目是否适合公开/私有
2. 创建 GitHub 仓库（与项目同名）
3. 初始化本地 git（如果还没有）
4. 添加 remote 并推送初始提交

### 示例
```bash
# 创建 GitHub 仓库
gh repo create project-name --public --source=~/src/project-name --push

# 或私有仓库
gh repo create project-name --private --source=~/src/project-name --push
```

### 命名映射
- 项目目录名 → GitHub 仓库名（自动转换连字符）
- 例如：`my-project` → `my-project`
