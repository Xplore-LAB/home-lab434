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

## OpenClaw 默认模型 = 本机 Qwen3.6-35B-A3B-NVFP4（2026-10-19 已切换）

- **默认路由**：`agents.defaults.model = {"primary": "local-qwen36/Qwen3.6-35B-A3B-NVFP4", "fallbacks": ["minimax/MiniMax-M3.1-Flash-Preview"]}`；别名 `Qwen36`。fallback 是刻意留的云端兜底——本地 vLLM 挂了不至于整个会话断掉。
- **Provider 配置**：`models.providers.local-qwen36`，`baseUrl = http://127.0.0.1:8000/v1`，`api = openai-completions`。**整个 provider 必须一次 `openclaw config set` 写入**（baseUrl/api/apiKey/models 一起），分次写会被校验器逐个拒掉：缺 models 报 "must declare models"，缺 baseUrl 报 "must declare baseUrl"。
- **密钥**：vLLM 侧 `--api-key` 写在 `~/models/Qwen3.6-35B-A3B-NVFP4-docker-compose.yml` 里；抽出来存成 `~/.openclaw/secrets/local-qwen36.key`（0600），再走 `secrets.providers.local_qwen36_key_file` 文件型 SecretRef 挂到 `models.providers.local-qwen36.apiKey`。值不落 config 明文。
- **该模型实测能力**（vLLM 0.1.dev19043，262k ctx，qwen3_xml tool parser）：chat ✅、tool call ✅、图片输入 ✅（Qwen3.6 是多模态，config.json 里有 visual tower）、reasoning ✅（`reasoning_effort` 和 `chat_template_kwargs.enable_thinking` 两种写法都接受，返回在 `reasoning` 字段）。注意容器默认 `--default-chat-template-kwargs={"enable_thinking":false}`，即 thinking 默认关，要思考得显式传参。
- **本机端点分工**（别搞混）：`:8000` = Qwen3.6 NVFP4 主服务（root 起的 vLLM，带 key）；`:8001` = xiyangyang 的 nl2_sql uvicorn；`:8080` = 另一个带鉴权的服务；`:8015` = docker 里给 paper-01 用的 Qwen2.5-Coder-1.5B。
- **排查坑**：`openclaw agent --agent <id>` 从 exec 里调会被拦（"Gateway agent from agent exec would lose inter-session attribution"）；`openclaw infer model run --gateway` 也一样。**验证要改成 `sessions_spawn`（isolated 子会话）** 才能跑通真实 agent 回合。

## mihomo 代理：主节点 + 订阅备份（2026-10-19 改造）

- **拓扑（2026-10-21 现状）**：`🐟 漏网之鱼` → `🚀 节点选择`(watcher 切换点) → `⭐ 主节点`(= `🇸🇬 新加坡优选` url-test) 或 `♻️ 全球优选`(url-test，含 US 节点)
- **用户唯一诉求：尽量稳定**。所有参数围绕这一条调，不要加花哨功能。
- **主节点 = 新加坡组**（用户指定「新加坡优化GPT挺好的」）。`♻️ 全球优选` 池含 24 个非新加坡订阅节点 **+ US 节点**（跨供应商冗余，关键：避免兜底兜回同一个坏源）。
- **关键认知：所有机场线路都是双峰形态**——要么 ~500ms，要么 4000-5600ms，中间无过渡。`新加坡-优化2-GPT` 确认长期死亡（多次探活全 0）。订阅源会持续劣化：2026-10-19 16/27 可用 → 21:18 12/27。**晚高峰后未恢复，是结构性劣化不是波动。**
- **旧 US 节点 `[US]-150.241.187.96`**：VLESS+REALITY，24 次采样跨 516–5903ms，零次稳定；但状态好时能到 580ms（比订阅最快还快）。已降为跨源兜底，**不要当主力**。
- **全量扫描结果（27 个订阅节点，16 可用）**：香港WAP-优化 208 / 台湾-优化 272 / 香港WAP-优化3 651 / 台湾-优化3 655 / 日本-优化3 830 / 印度-优化 945 / 美国LA-优化3-GPT 1016 / 新加坡-优化3 2921 / 加拿大-优化 5375。**新加坡是这批里最慢的一档**，用户原话要求“优先新加坡”，但实测比香港慢 14 倍——已告知并把香港提为主节点、新加坡降为备份第一档。
- **关键：OpenAI/Codex 流量必须走 `-GPT` 后缀节点，否则 Cloudflare 403**。普通节点一律 403；`-GPT` 节点返回 405(GET 打 POST 端点) 或 401(缺鉴权) = 正常。**普通连通性测试（google/HF 200）测不出这个差异**，必须直接打 `https://chatgpt.com/backend-api/codex/responses` 才能发现。
- **已实测的 GPT 节点可用性（2026-10-21）**：能用 = 新加坡-优化-GPT、美国LA-优化-GPT、美国LA-优化3-GPT、英国-优化-GPT；**死的（000/超时）= 新加坡-优化2-GPT、台湾-优化2-GPT、美国LA-优化2-GPT**。已在 `🔐 GPT优选` 组用 `exclude-filter: "优化2"` 排掉后者。
- **mihomo 规则指向组**：给 OpenAI 域名单独指派 `🔐 GPT优选` 组，其余流量走主路由。规则必须在 MATCH 之前。
- **踩坑：mihomo 的组探活 `/proxies/{group}/delay` 不可用**。组内只要有一个死成员（如 `新加坡-优化2-GPT`）永远不回，整个请求就被拖到 API 超时并返回 `{"message":"Timeout"}`，无法区分「组内全死」和「有个死成员」。只探组当前选中的那条也不行——选中项可能正是死的那条。**正解：逐个成员探活、跳过超时的、取最小正延迟**；全部不达标才判 FAIL，读不到组 JSON 才判 UNKNOWN。
- **坑：探活超时不能当成失败**。把 timeout 类错误当失败会误清零已攒的稳定计时（实测因此白白清了 9 分钟）。但反过来「全部成员都超时」= 组真的不可用了，必须判 FAIL 降级。判据分清：读不到组本身→UNKNOWN（不判节点死活）；有成员达标→健康；无一达标→FAIL。
- **踩坑：provider 节点不能按名字在 `proxies:` 里引用**。`proxy-providers` 里的节点只能用 `use:` + `filter` 引入组；想锁定某一个就用 `type: select` + `use: [subscription]` + `filter: "^香港WAP-优化$"`。写成普通 `proxies:` 会报 `'<name>' not found`。
- **踩坑：选择器默认选中第一项**。把 `⭐ 主节点` 放在 `🚀 节点选择` 第一位会让 mihomo 启动就切到主节点，**绕过 10 分钟稳定门槛**。第一项必须是 `♻️ 备用通道`。
- **备份订阅**：27 个真实 vmess 节点（日本/新加坡/香港/台湾/美国LA/加拿大/德国/英国/印度），其中 7 个 GPT 优化线路。实测可用：出口 `45.149.92.22`，延迟 ~614ms，google 204 / huggingface 200。
- **踩坑：订阅里的前 3 条是伪节点**（`剩余流量：xxx` / `套餐到期` / `过滤掉N条线路`），指向真实服务器所以能“连通”，不过滤会被当节点选中。已用 `proxy-providers.exclude-filter: "剩余流量|套餐到期|过期|过滤掉"` 排除。
- **踩坑：mihomo 的 fallback 组无法表达“稳定 N 分钟才切回”**。`interval` 同时控制“多久发现故障”和“多久考虑切回”，两者耦合：interval 小 → 故障转移快但切回频繁；interval 大 → 切回慢但故障转移也慢（实测 interval=600 时主节点死了最多卡 10 分钟，境外全断 HTTP=000）。严格语义必须外挂 watcher。
- **应急手法**：主节点挂了不用等 interval，用控制 API 强制探活可立即切走：`curl "http://127.0.0.1:9090/group/<组名URL编码>/delay?timeout=5000&url=..."`
- 配置文件 `~/.config/mihomo/config.yaml`（含订阅 token，已设 `chmod 600`）；原始配置备份在 `config.yaml.bak.20261019-165132`。

## 本地已验证的 GPU PyTorch 环境（全局可用）

- **路径**：`/home/lab434/apps/ai-services/vllm-env`
- **版本**：`torch 2.11.0+cu130`，`cuda 13.0`
- **硬件**：`NVIDIA GB10`，`torch.cuda.is_available() = True`
- **验证命令**：`/home/lab434/apps/ai-services/vllm-env/bin/python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"`
- **意义**：后续本地训练/微调/rollout 优先用这个 venv，不要再从零装 PyTorch。

## DeepInfer 源码已落地本机，但架构不匹配（2026-10-24）

- **官方仓库是 `deepseek-ai/DeepInfer`**（不是 Xperience1112/DeepInfer，那个 404）；Apache-2.0，21.5k star，HEAD `9bd9cf2`。
- **本地路径** `~/src/deepinfer`（644 MB），6 个 vendor 子模块 + 嵌套共 16 个 submodule 全部拉到 pinned commit，工作树干净。构建顺序由 `build.sh` → `scripts/build_vendor.sh` 决定：DeepSelect → FlashMLA → DeepEP → DeepGEMM，每个编成 wheel 再装。
- **sdist**：`~/data/downloads/deepinfer-0.1.0.tar.gz`（0.6 MB，sha256 `959b9bd010893b4c6dc60be0dd822e10e7f1ae1e53289233a83741f76c3d681a`）。PyPI 只有 sdist 没 wheel，且 `pip install` 会拉 torch 2.13.0+cu132（高于本机 2.11.0+cu130），所以别用 pip 装。
- **硬阻塞（架构，不是缺依赖）**：DeepInfer 官方只支持 **NVIDIA SM100**（数据中心 Blackwell）或 **昇腾 950**。本机 GB10 是 **compute capability 12.1 / sm_121**，FlashMLA、DeepGEMM 这类 vendored kernel 面向 sm_100a，编不过或跑不对。工具链本身齐全（CUDA 13.0.88、gcc 13.3、Python 3.12.3、torch 2.11.0+cu130），要跑必须改 arch flag 往 sm_121 移植，DeepGEMM 还要确认 CUTLASS/PTX 路径，工作量大且成功率不确定。
- **结论**：本机要用 DeepSeek-V4.1-Flash 推理，走已跑通的 vLLM/SGLang 路线（见 `~/src/dgx-spark-vllm-*`、`~/src/qwen38-sglang-deploy`）远比硬啃 DeepInfer 划算。DeepInfer 这份源码留作参考/二次开发底座。
