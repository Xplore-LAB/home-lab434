# Home Lab 434

一个基于 NVIDIA GB10 的个人 AI 实验室。本地跑模型、做研究、接传感器、偶尔写点工具。

---

## 硬件

- **主机**：NVIDIA GB10（单卡，arm64）
- **GPU**：NVIDIA，CUDA 13.0，PyTorch 2.11.0+cu130
- **验证环境**：`/home/lab434/apps/ai-services/vllm-env`

```bash
/home/lab434/apps/ai-services/vllm-env/bin/python -c \
  "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
# torch 2.11.0+cu130 cuda 13.0 True
```

## 本地模型服务

- **Qwen3.6-35B-A3B-NVFP4**：通过 DeepSeek Harness（dsh）的 `local-qwen` provider 在 `localhost:8000` 提供 OpenAI 兼容接口
- **公网暴露**：cpolar 隧道 `pse434.vip.cpolar.cn` → localhost:8000，Bearer 认证
- **mDNS 发现**：`local-ai-discovery` 广播本地服务，`local-ai-dsh-sync` 做用户态同步

```bash
# 测试
curl https://pse434.vip.cpolar.cn/v1/models \
  -H "Authorization: Bearer $(cat ~/.dsh/.env | grep LOCAL_AI_KEY | cut -d= -f2)"
```

## 项目

### MiMo-V2.6-RL-oss 本地环境
Docker 复刻 K8s pod 拓扑，跑 MiniMax 的 RL 任务实例。侧边car 容器负责判分，workspace 同步进 sidecar 才能拿到有效 reward。

- **首次满分**：`s3k_0000_accounting_audit_tax_en_t1_rl_008`，reward = 1.0
- **关键排障**：sidecar 读 `/work/workspace/answer.md`，main 容器必须 `tar cf` → 宿主机中转 → sidecar 解包
- **MCP 服务**：`mimo-mcp-arm`（原生 arm64）提供 4 个工具服务，端口 39101–39104
- **副本目录**：`rl-lab/mimo-docker/out/<instance>/`

### Agent Toolkit
Agent 开发脚手架和工作规范，放在 `agent-toolkit/`。不是框架，是写 Agent 时踩过的坑和形成的习惯。

- `scaffold/`：项目模板
- `FILE-MAP.md`：目录规范
- `BEST_PRACTICES.md`：文件操作最佳实践
- `run_experiments.py`：MiMo 实验工具
- `batch_experiments.sh`：批量实验脚本

### 传感器与工业数据
- **烟草大棚传感器**：12 节点 LoRa 网络，监控温湿度。半数节点已离线，日志保留在 `memory/` 中
- **空分装置数据**：`河南杭氧 30000` 制氧装置 DCS 数据，氧纯度、导叶开度、下塔液空等参数分析

### Career Advisor Agent
个人职业顾问 Agent，基于 OpenClaw 工作区规范，管理求职流程和职位追踪。

## 目录结构

```
home-lab434/
├── agent-toolkit/     # Agent 开发工具和模板
├── career-advisor/    # 职业顾问 Agent 配置
├── docs/              # 调研文档
├── memory/            # 日常笔记和经验沉淀
├── research/          # 研究报告
├── scripts/           # 实用脚本
├── AGENTS.md          # 工作区规范
├── MEMORY.md          # 长期记忆
├── SOUL.md            # 人格/风格
└── USER.md            # 用户偏好
```

## 环境变量和密钥

- **MiniMax API Key**：`~/.openclaw/secrets/minimax.key`（chmod 600）
- **Dsh 本地服务**：`~/.dsh/.env`（cpolar tunnel key）
- **GitHub CLI**：已认证，scopes 完整

## 哲学

这个仓库不是产品，是我的工作台。里面有整理好的东西，也有正在试的东西。文档和代码一样重要——六个月后我会感谢现在的自己写了注释。

---

*最后更新：2026-10-07*
