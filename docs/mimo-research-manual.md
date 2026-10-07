# MiMo / verl 研究者手册

> 目标：先搞清楚“能做什么”，再结合本地环境和算力决定“先做什么”。  
> 最后更新：2026-10-07

---

## 1. 我们有什么

### 1.1 代码与框架
- **MiMo-verl**：`src/research/rl-lab/MiMo-verl`
  - 基于 verl（ByteDance HybridFlow）二次开发
  - 开源 5 个 agentic RL 环境：Code / Cyber / General / Visual / Music
  - 每个 domain 都有独立的 recipe、config、launch script
- **mimo-docker**：`src/research/rl-lab/mimo-docker`
  - 本地已跑通的 Docker 环境 + rollout + verify 全流程
  - 解决了 MCP SDK 兼容、workspace 同步、端口映射等坑
- **公开数据集**：`data/datasets/MiMo-V2.6-RL-oss`
  - parquet 格式，覆盖 5 个 domain
  - 可用 `pyarrow` 直接查询 instance 元数据

### 1.2 关键脚本与配置
| 路径 | 用途 |
|---|---|
| `MiMo-verl/recipes/*/config/*.yaml` | 各 domain 的训练超参 |
| `MiMo-verl/recipes/*/agent_loop.py` | agent 循环实现 |
| `MiMo-verl/recipes/*/reward.py` | reward 计算 |
| `mimo-docker/mimo_env_runner.py` | 环境生命周期（up/ports/verify/down） |
| `mimo-docker/rollout2.py` | 本地 rollout 循环（bash + MCP） |
| `MiMo-verl/scripts/*/train.sh` | 官方训练 launch script |

### 1.3 已验证的本地经验
- `mimo-mcp-arm` 容器提供 MCP 工具服务，避开 emulated amd64 容器 pip 卡死问题
- verify 前必须把 main 容器 workspace tar 同步到 sidecar，否则 reward=0.5
- Judge 用 MiniMax-M3 + `chat` API（不是 `responses`）

---

## 2. 能做什么（研究方向）

### 2.1 复现 & 基准测试（最小可行）
**做什么**：用官方 parquet + 官方 Docker 环境，跑标准 rollout → verify → reward。  
**参考**：`mimo-docker/EXPERIMENT_SOP.md` Section 9、10。  
**起步**：
1. 从 `general` domain 挑 10 个 instance
2. 跑 `rollout2.py --max-steps 60`
3. 记录 reward 分布
4. 做 1 个消融（如 temperature=1.0 vs 0.6）

**产出**：本地 baseline 报告，包括 reward 分布、失败 case 分析、耗时统计。

---

### 2.2 新任务 / 领域迁移
**做什么**：把自定义业务任务封装成 MiMo 支持的格式，复用其 Docker + MCP + verifier 基础设施。  
**参考**：
- `recipes/general/`（知识工作，rubric judging）
- `recipes/design/webdev/`（视觉/网页）
- `recipes/arvo/`（规则检查）
- `mimo-docker/EXPERIMENT_SOP.md` Section 3（元数据格式）

**起步**：
1. 准备 task 描述 + workspace 模板 + verifier（rubric / rule / test）
2. 写成 parquet 或直接用本地 task dir
3. 复用 `mimo_env_runner.py` 起环境
4. 复用 `rollout2.py` 或自写 agent loop

**产出**：1 个新的 domain recipe，能在本地跑通 verify。

---

### 2.3 算法消融 & 改进
**做什么**：在官方 GRPO 配置基础上，调整 reward、采样、长度惩罚等，验证对 agent 性能的影响。  
**参考**：`recipes/*/config/*.yaml` 中的可调参数。  
**可调旋钮举例**：
| 参数 | 含义 | 快速验证 |
|---|---|---|
| `algorithm.length_penalty.*` | 长度惩罚 | enable=true vs false |
| `algorithm.filter_groups.enable` | GRPO group 过滤 | true vs false |
| `rollout.temperature / top_p / top_k` | 采样策略 | 1.0/0.95/-1 vs 0.6/0.95/20 |
| `multi_turn.format` | 对话格式 | qwen3_coder vs 其他 |
| `actor.entropy_coeff` | 熵系数 | 0 vs 0.01 |

**起步**：
1. 选 1 个 domain（推荐 General，环境最轻量）
2. 复制官方 yaml，改 1 个参数
3. 用官方模型做 rollout 对比
4. 统计 reward、响应长度、工具调用成功率

**产出**：消融实验报告，指出哪些参数对 agent 行为影响最大。

---

### 2.4 系统效率 & Rollout 优化
**做什么**：优化 rollout 吞吐量、降低环境启动时间、提高并行度。  
**参考**：
- `mimo-docker/EXPERIMENT_SOP.md` Section 4.1（up 优化历史）
- verl 官方文档：`workers/sglang_worker.html`、`perf/perf_tuning.html`
- 社区博客：Optimizing SGLang Memory Usage、verl x SGLang Multi-turn Code Walkthrough

**可研究点**：
- 不同 rollout engine（vLLM / SGLang / HF）在本地 arm64 上的延迟对比
- `mimo-mcp-arm` 共享策略 vs 每 instance 独占
- workspace 同步方案优化（rsync vs tar vs volume mount）
- TransferQueue / uni-agent 轨迹复用对吞吐量的影响

**起步**：
1. 测量当前单 instance 的 up/rollout/verify 耗时
2. 尝试并行启动 2-4 个 instance
3. 对比不同 MCP 服务部署方式

**产出**：性能基准 + 优化建议。

---

### 2.5 失败模式 & 可解释性分析
**做什么**：分析 rollout 失败原因，理解 agent 决策过程。  
**参考**：`reward_detail.json` 结构（SOP Section 4.4）。  
**可研究点**：
- 哪类 rubric item 最容易丢分
- 工具调用失败模式统计（bash 错误 / MCP timeout / 输出格式错误）
- 响应长度 vs reward 相关性
- 多轮对话中，哪一步开始偏离正确路径

**起步**：
1. 收集 20-50 个 instance 的 `reward_detail.json`
2. 按 rubric item 聚合得分
3. 分析失败 case 的 rollout 日志

**产出**：失败模式 taxonomy + 改进建议。

---

### 2.6 安全 & 对齐研究（尤其 Cyber 域）
**做什么**：研究 agent 在漏洞复现任务中的安全边界。  
**参考**：`recipes/arvo/`、社区项目如 GUI-R1、Agent Lightning。  
**可研究点**：
- 模型是否会生成 exploits 并在非受控环境中执行
- reward hacking：模型发现规则漏洞但未真正修复
- 安全护栏：在 rollout 中限制危险命令（rm -rf / curl | sh / 网络扫描）
- judge 鲁棒性：rubric 是否会被特定输出模式欺骗

**起步**：
1. 选 5-10 个 Cyber instance
2. 人工审查 rollout 轨迹中的危险命令
3. 设计简单的安全过滤器并测试对 reward 的影响

**产出**：安全风险评估报告 + 护栏设计建议。

---

## 3. 本地环境约束与算力适配

### 3.1 已知约束
- 主机：`spark-44a8`，aarch64，通过 QEMU 运行 linux/amd64 镜像
- 单机 GPU 资源有限，不适合直接跑官方 Megatron 多节点训练
- 但适合：单节点 rollout、算法原型验证、数据收集、消融实验

### 3.2 适配策略
| 官方场景 | 本地替代方案 |
|---|---|
| 4-8 节点 Megatron 训练 | 用 FSDP 单机多卡，或改用 SGLang async rollout |
| 大规模数据采样 | 先在小批量 parquet（10-50 条）上验证算法 |
| 模型微调 | 用 LoRA / 小 batch 降低显存需求 |
| 多环境并行 | 用 `mimo-mcp-arm` 共享 + Docker 批量启动 |

### 3.3 推荐起步配置
- Domain：General（环境最轻量，无需 GPU 即可 verify）
- 数据量：10-20 instance
- Rollout：`rollout2.py --max-steps 60`
- 模型：MiniMax-M3（已有 key）或本地小模型
- 评估：reward 分布 + 失败 case 分析

---

## 4. 下一步行动建议

1. **本周**：跑通 General domain 10 instance baseline，输出 reward 分布
2. **下周**：选 1 个消融方向（temperature / length penalty），做对比实验
3. **月底**：根据 baseline 结果，决定是否扩展到 Code/Visual 或尝试算法改进

---

## 5. 参考资料索引

- MiMo 技术报告：https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL/blob/main/MiMo_V2_6_technical_report.pdf
- verl 官方文档：https://verl.readthedocs.io/
- 公开数据集：https://huggingface.co/datasets/XiaomiMiMo/MiMo-V2.6-RL-oss
- 训练模型：https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B
- Docker 镜像：https://hub.docker.com/r/xiaomimimo/mimo-v2.6-rl-oss
- 社区项目列表：见 `MiMo-verl/README.md` Awesome Projects 章节
