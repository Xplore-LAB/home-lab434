# MEMORY.md - Durable Facts and Decisions

<!-- project: path:/home/lab434/.openclaw/workspace -->

## /home/lab434 目录整理方法论（2026-10-05）

- **原则**：只归并、不删除；不动隐藏配置目录（`.openclaw`、`.config`、`.cpolar`、`.ssh` 等）；不动用户目录（`Desktop`、`Downloads`、`文档`、`图片` 等）
- **标准结构**：`projects/`（项目代码）、`models-deploy/`（模型部署）、`ai-services/`（AI 服务脚本）、`minimax-workspace/`（MiniMax/H3）、`data/`（数据与知识）、`research/`（研究与实验）、`deploy/`（部署脚本）
- **执行顺序**：先创建目标目录 → 再移动 → 清理空目录 → 验证结果
- **排障经验**：`mv` 前先检查目录是否存在；使用 `set -e` 时要注意错误处理；后台任务完成后要验证结果；保留原始备份
- **记忆文件**：详细方案见 `memory/home-lab434-organization-plan.md`

---

## MiMo-V2.6-RL-oss 本地环境（rl-lab）——2026-09-30 首次满分

- **结果**：实例 `s3k_0000_accounting_audit_tax_en_t1_rl_008`（Agree Realty / Fairfax & 3rd 交割就绪任务）双容器拓扑跑通，verifier **6/6 全过，`reward.json` = `{"reward": 1.0}`**；副本 `rl-lab/mimo-docker/out/<instance>/`。
- **排障权重最高的一条（教训）**：判分在 **sidecar** 容器执行，读 `/work/workspace/answer.md`。纯 Docker 复刻 K8s pod 时，**必须把 workspace 同步进 sidecar**（main `tar cf` → 宿主机中转 → sidecar 解包），否则 sidecar 的 workspace 是空目录，judge 每轮看空证据，所有 llm 项恒 0——**答案质量与分数无关**。曾据此误判过两轮（先怪步数、再怪答案没对账 DealCloud），都是错的。
- **MCP 实况**：4 个工具服务实际在 `mimo-mcp-arm`（原生 arm64，mcp 1.30.0）的 39101–39104，宿主映射 39111–39114；主容器的同名端口是空发布。`mcp_bridge.py` 原本只在主容器，`docker cp` 不支持容器间直拷，需宿主机中转。
- **判分口径**：交易级 DTT $9,141/$37,395/$46,536 才是推荐交易（DC-TXN-25Q3-024）的 approved 值，案例级汇总 22341/91395/113736 是另一套；买家偿付力 complete 行只挂已被取代的股权转让交易（DC-TXN-25Q3-021）；受控金额取 SharePoint DEC-2025-017（$7,183,750+$21,551,250），与 DealCloud 行的 $8,310,000/$6,000,000 故意不一致。
- ** judge 配置**：MiniMax `GA_JUDGE_API=chat`（默认 responses 失败），URL `https://api.minimaxi.com/v1`，key 从 `~/.openclaw/secrets/minimax.key` 读，不落盘。
- **待办**：workshop 托管 skill `mimo-rl-env-runner` 的 SKILL.md 缺「sidecar 同步 workspace」步骤，已记录待用户授权后走 skill_workshop 提案；三个 mimo 容器仍 Up，是否 down 待用户定。

## 本地已验证的 GPU PyTorch 环境（全局可用）

- **路径**：`/home/lab434/apps/ai-services/vllm-env`
- **版本**：`torch 2.11.0+cu130`，`cuda 13.0`
- **硬件**：`NVIDIA GB10`，`torch.cuda.is_available() = True`
- **验证命令**：`/home/lab434/apps/ai-services/vllm-env/bin/python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"`
- **意义**：后续本地训练/微调/rollout 优先用这个 venv，不要再从零装 PyTorch。
