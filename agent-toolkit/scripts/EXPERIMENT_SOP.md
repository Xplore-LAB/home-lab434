# MiMo-V2.6-RL 论文实验 SOP

> 基于 `spark-44a8`（`aarch64`，QEMU 运行 `linux/amd64` 镜像）实测收敛。
> 最后验证：`2026-10-05 20:48 CST`，`s3k_0000_accounting_audit_tax_en_t1_rl_008`，`reward=1.0`（6/6）。

## 1. 目录结构

```
/home/lab434/rl-lab/mimo-docker/
├── mimo_env_runner.py        # 环境生命周期：list / up / ports / verify / e2e / down
├── rollout2.py               # 策略循环（bash + MCP）→ /work/workspace/answer.md
├── agent_rollout.py           # 早期极简 rollout，保留作对照
├── pull_deep.py              # 调试用：逐笔拉 DealCloud 明细
├── pull_dealcloud.py         # 调试用：拉 DealCloud 对账
├── logs/                     # 运行日志（归档到 logs/archive/）
├── out/                      # 每 instance 结果：reward.json / reward_detail.json
└──  README.md                # 本文件

/data/MiMo-V2.6-RL-oss/
├── general/train.parquet     # 925 general_agent + 64 terminal_bench 行
├── general/envs/             # 每 instance 的 task dir（workspace / system / tools）
├── README.md
├── code.parquet / cyber.parquet / webdev.parquet / music.parquet
└── image-mapping.jsonl
```

## 2. 前置检查

```bash
# 2.1 Docker
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' | head

# 2.2 Dataset
ls /home/lab434/datasets/MiMo-V2.6-RL-oss/general/train.parquet
python3 -c "import pyarrow.parquet; print('pyarrow ok')"

# 2.3 Judge key
ls -l /home/lab434/.openclaw/secrets/minimax.key
MINIMAX_API_KEY=$(cat /home/lab434/.openclaw/secrets/minimax.key)
```

## 3. 实例元数据查询

```python
# 查询 instance 的 docker_image / env_task_dir / cwd / wait_ports
cd /home/lab434/datasets/MiMo-V2.6-RL-oss && python3 - <<'PY'
import pyarrow.parquet as pq, json
IID = "s3k_0000_accounting_audit_tax_en_t1_rl_008"
for r in pq.read_table('general/train.parquet').to_pylist():
    ei = r['extra_info']; ei = json.loads(ei) if isinstance(ei, str) else ei
    ij = ei.get('instance_json') or {}; ij = json.loads(ij) if isinstance(ij, str) else ij
    if ei.get('instance_id') == IID:
        print(json.dumps({k: ij.get(k) for k in
              ('dataset_type','docker_image','env_task_dir','cwd','verifier_timeout_sec')}, indent=2))
PY
```

通用字段：
| 字段 | 含义 |
|---|---|
| `dataset_type` | `general_agent`（两容器）/ `terminal_bench`（单容器） |
| `docker_image` | `general-agent-env-0:oss` → pull ref: `xiaomimimo/mimo-v2.6-rl-oss:general-agent-env-0` |
| `env_task_dir` | 相对于 `general/` 的路径，如 `envs/s3k_0000_accounting_audit_tax_en_t1_rl_008` |
| `cwd` | 容器内工作目录，通常是 `/work/workspace` |
| `wait_ports` | manifest 里的 MCP 端口列表，默认 `[39101,39102,39103,39104]` |

## 4. 环境生命周期

### 4.1 Up（两容器 + MCP 工具）

**重要**：通用镜像的 MCP SDK 版本太新，sidecar 内直接启动 MCP 服务会崩溃。  
**标准做法**：用一个原生 `python:3.11-slim-bookworm` 容器（`mimo-mcp-arm`）统一提供 MCP 工具服务，端口映射到宿主机。

```bash
# 4.1.1 确认现有容器可用，或重建
docker ps --filter 'name=mimo' --format '{{.Names}}\t{{.Status}}'

# 4.1.2 如需重建（注意：会丢失旧容器内数据！）
python3 mimo_env_runner.py down --instance <IID>
python3 mimo_env_runner.py up --instance <IID>
```

**重建会执行**：
1. `main` 容器启动，mount `task_dir/workspace`，发布 39101-39104
2. `sidecar` 容器加入 main 网络命名空间，mount `task_dir/system` + `task_dir/tools`
3. 投放 `sidecar_entrypoint.py` / `mcp_http.py` / `mcp_bridge.py`
4. 执行 manifest 的 setup 命令（已知失败，忽略）
5. 等待 wait_ports

**实际 MCP 服务** 由 `mimo-mcp-arm` 提供（见 `SECTION 5`），与 main/sidecar 并行运行。

### 4.2 Ports 检查

```bash
python3 mimo_env_runner.py ports --instance <IID>
# 期望：39101-39104 全部 OK
```

**注意**：如果 `mimo-mcp-arm` 映射了宿主机 39111-39114（或同端口），则 main 无法再发布 39101-39104。  
当前 spark-44a8 配置：`mimo-mcp-arm` 用 `39111-39114`，main 用 `39101-39104`，无冲突。

### 4.3 Workspace → Sidecar 同步（CRITICAL）

**每次 verify 前必须同步！** Verifier 运行在 sidecar 内，读的是 sidecar 的 `/work/workspace`，不是 main 的。

```bash
docker exec <main> tar cf /tmp/ws.tar -C /work workspace
docker cp <main>:/tmp/ws.tar /tmp/ws.tar
docker cp /tmp/ws.tar <sidecar>:/tmp/ws.tar
docker exec <sidecar> tar xf /tmp/ws.tar -C /work
docker exec <sidecar> wc -c /work/workspace/answer.md   # 验证非空
```

跳过此步 → `reward=0.5`（source_data_present 通过，5 个 llm 全部 0 票）。

### 4.4 Verify

```bash
GA_JUDGE_URL=https://api.minimaxi.com/v1 \
GA_JUDGE_KEY="$(cat /home/lab434/.openclaw/secrets/minimax.key)" \
GA_JUDGE_MODEL=MiniMax-M3 \
GA_JUDGE_API=chat \
  python3 mimo_env_runner.py verify --instance <IID>
```

**参数说明**：
| 环境变量 | 值 | 必填 |
|---|---|---|
| `GA_JUDGE_URL` | `https://api.minimaxi.com/v1` | ✅ |
| `GA_JUDGE_KEY` | MiniMax API key | ✅ |
| `GA_JUDGE_MODEL` | `MiniMax-M3` | ✅ |
| `GA_JUDGE_API` | `chat`（**不要** `responses`） | ✅ |
| `VERIFY_DETERMINISTIC` | `1` | 可选（runner 默认注入） |
| `VERIFY_AGENT_JUDGE` | `1` | 可选（runner 默认注入） |

**输出**：
- `out/<IID>/reward.json` — `{"reward": 1.0}` 或 `{"reward_error": "judge_crashed"}`
- `out/<IID>/reward_detail.json` — 各 rubric item 的得分详情

**Score 解读**：
| reward | 含义 |
|---|---|
| `1.0` | 6/6 通过 |
| `0.5` | `source_data_present` 通过，llm 判分 0 票（先查 sidecar workspace 同步） |
| `0.0` + `judge_crashed` | Judge 配置缺失或 key 无效 |

### 4.5 Down

```bash
python3 mimo_env_runner.py down --instance <IID>
# 同时清理 mimo-mcp-arm（如果需要）
docker rm -f mimo-mcp-arm
```

## 5. MCP 工具服务（`mimo-mcp-arm`）

**启动**（仅需一次，多个 instance 共享）：

```bash
TD=/home/lab434/datasets/MiMo-V2.6-RL-oss/general/envs/<IID>
docker run -d --name mimo-mcp-arm \
  -p 39111:39101 -p 39112:39102 -p 39113:39103 -p 39114:39104 \
  -v "$TD:/work" \
  python:3.11-slim-bookworm sleep infinity

# 安装 mcp<2（兼容 v1 API）
docker exec mimo-mcp-arm python3 -m pip install --no-cache-dir 'mcp<2'

# 创建 venv 兼容符号链接 + 投放 payload 脚本
docker exec mimo-mcp-arm sh -lc '\
  mkdir -p /installed-agent /opt/openai-agents-venv/bin /logs/verifier && \
  ln -sf "$(command -v python3)" /opt/openai-agents-venv/bin/python && \
  cp /work/mcp_http.py /work/sidecar_entrypoint.py /installed-agent/'

# 启动 MCP 服务器
docker exec -d mimo-mcp-arm sh -lc 'cd /work && python3 /installed-agent/sidecar_entrypoint.py --start-and-detach > /tmp/entry.log 2>&1'
docker exec mimo-mcp-arm tail -c 600 /tmp/entry.log   # expect: [sidecar] all MCP servers ready
```

**验证工具可用**：

```bash
docker exec mimo-mcp-arm python3 /work/mcp_bridge.py \
  --url http://127.0.0.1:39101/mcp --name <server> --list
# expect: __MCP_ONESHOT__{"ok": true, "tools": [...]}
```

**为什么需要这个容器**：
- 通用镜像的 mcp SDK 是 2.2.0，而任务 payload 用 v1 API（`streamablehttp_client`、`FastMCP`）
- 在 emulated amd64 容器内 `pip install mcp<2` 会卡住（QEMU + pip 超时）
- 原生 arm64 容器避开这个问题

## 6. Rollout Loop（`rollout2.py`）

```bash
python3 rollout2.py --instance <IID> --max-steps 60 --model MiniMax-M3
```

**关键机制**：
- MiniMax-M3 作为 policy model，通过 `https://api.minimaxi.com/v1/chat/completions` 调用
- Tool 1: `bash` — 在 main 容器内执行命令（cwd `/work/workspace`）
- Tool N: MCP 工具 — 通过 `mimo-mcp-arm` 的 bridge 调用
- 前 12 步必须写入 `answer.md`（硬约束，第 14 步 nudge）
- 预置 digest：`struct_text.txt`（38KB 纯文本）作为第一条 user 消息，避免反复 cat 大文件
- 噪声过滤：自动剥掉 `x86_64-binfmt-P: QEMU internal SIGSEGV` 等仿真噪声
- 兜底：如果 loop 结束时 `answer.md` 缺失，从最终 chat 回复写入

**独立 launch（非阻塞）**：

```bash
setsid nohup python3 -u rollout2.py \
  --instance <IID> --max-steps 60 --model MiniMax-M3 \
  > logs/rollout2_<IID>_<YYYYMMDD>.log 2>&1 < /dev/null &

pgrep -f '[r]ollout2.*<IID>'   # 确认存活
tail -f logs/rollout2_<IID>_<YYYYMMDD>.log
```

## 7. 结果归档

每次 verify 后，确认以下文件已写入 `out/<IID>/`：

```
out/<IID>/
├── reward.json           # 最终 reward
└── reward_detail.json    # 各 item 详情
```

Rollout 日志：
```
logs/rollout2_<IID>_<YYYYMMDD>.log    # rollout 输出
```

**命名规范**：
- Instance: `s3k_0000_accounting_audit_tax_en_t1_rl_008`
- 日期：`YYYYMMDD`
- 日志：`rollout2_<IID>_<date>.log`
- 答案：容器内 `/work/workspace/answer.md` + 可导出到 `out/<IID>/answer.md`

## 8. 已知坑 & 避坑指南

| 坑 | 表现 | 修复 |
|---|---|---|
| Judge key 未注入 | `judge_crashed: no judge key` | 必须传 `GA_JUDGE_*` 环境变量 |
| `GA_JUDGE_API` 错误 | Judge 调用失败 | 用 `chat`，不是 `responses` |
| Sidecar workspace 不同步 | `reward=0.5`（5 个 llm 0 票） | verify 前执行 tar 同步 |
| Port 冲突 | `Bind for 0.0.0.0:39101 failed` | 统一用 `mimo-mcp-arm` 的 `39111-39114` |
| QEMU 噪声 | 模型以为命令失败 | `rollout2.py` 的 `NOISE_RE` 已过滤 |
| 镜像内 pip 卡住 | 安装 mcp<2 超时 | 不在 emulated 容器内 pip install |
| 容器名截断 | `No such container` | 用 runner 的 `containers(iid)` 函数获取全名 |

## 9. 实验 checklist（论文用）

每个 instance：
- [ ] 查询 parquet 元数据（image / task_dir / cwd / ports）
- [ ] 确认环境 up（`ports` 全部 OK）
- [ ] 确认 `mimo-mcp-arm` 运行且 `--list` 返回工具
- [ ] 运行 rollout（记录步数、时间、最终答案）
- [ ] **同步 workspace 到 sidecar**
- [ ] 运行 verify（传入 judge 配置）
- [ ] 记录 `reward.json`、`reward_detail.json`、rollout 日志
- [ ] 归档 `answer.md` 到 `out/<IID>/`

## 10. 对比实验模板

### 10.1 基线：zero-shot / few-shot（无 rollout）

直接用 MiniMax-M3 看 instruction + digest，写 `answer.md`，verify。

### 10.2 Rollout w/ MCP

`rollout2.py` 标准流程，60 步。

### 10.3 Ablation

| 实验 | 改动 |
|---|---|
| no-digest | `--no-digest`，看模型是否需要预提取文本 |
| no-sync | 故意跳过 sidecar 同步，验证 0.5 症状 |
| no-MCP | 禁用 MCP 工具，只用 bash + workspace |
| max-steps=12/24/60 | 步数预算影响 |

### 10.4 模型替换

```bash
python3 rollout2.py --instance <IID> --max-steps 60 --model <model_name>
```

需要同时改 `JUDGE_URL` / key（如果 judge 和 policy 用同一个 provider）。

## 11. 快速参考

```bash
# 列 instance
python3 mimo_env_runner.py list --limit 10

# 起环境
python3 mimo_env_runner.py up --instance <IID>

# 端口
python3 mimo_env_runner.py ports --instance <IID>

# 验证（带 judge）
GA_JUDGE_URL=https://api.minimaxi.com/v1 \
GA_JUDGE_KEY="$(cat /home/lab434/.openclaw/secrets/minimax.key)" \
GA_JUDGE_MODEL=MiniMax-M3 GA_JUDGE_API=chat \
python3 mimo_env_runner.py verify --instance <IID>

# Rollout
python3 rollout2.py --instance <IID> --max-steps 60 --model MiniMax-M3

# 关环境
python3 mimo_env_runner.py down --instance <IID>
```

---

文档生成时间：2026-10-05  
验证环境：`spark-44a8`，`aarch64`，Docker + QEMU  
最后成功：`s3k_0000_accounting_audit_tax_en_t1_rl_008`，`reward=1.0`（6/6）
