# /home/lab434 目录整理方案

<!-- observed: 2026-10-05 | status: active -->

## 原则

- 只归并、不删除
- 保留原目录内容完整性
- 不动隐藏配置目录：`.openclaw`、`.config`、`.cpolar`、`.ssh`、`.local`、`.npm-global`、`.cache`
- 不动用户目录：`Desktop`、`Downloads`、`文档`、`图片`、`视频`、`音乐`、`公共`、`模板`、`Android`

## 标准结构

```
/home/lab434/
├── projects/           # 项目代码
│   ├── nav-server/
│   ├── careerflow-agent/
│   ├── llm-tracker/
│   ├── air-separation-project/
│   ├── airsep-copilot/
│   ├── chat-tts-ui/
│   ├── voice-assistant/
│   ├── postbird/
│   ├── xi yangyang/
│   ├── verl-agent/
│   ├── rl-grpo-air-nl2sql/
│   ├── openrlhf-project/
│   ├── dsh-plugin-asmemory/
│   ├── embedding-docker/
│   ├── mobileforge/
│   ├── graphrag/
│   ├── knowledge/
│   ├── kg/
│   ├── zhishitupu/
│   ├── zju-autologin/
│   ├── zju-web-login/
│   ├── napcat-data/
│   └── ...
├── models-deploy/      # 模型部署
│   ├── models/
│   ├── models-local-qwen38/
│   ├── qwen38-sglang-deploy/
│   ├── dgx-spark-vllm-dflash/
│   ├── dgx-spark-vllm-qwen3.6-35b-a3b-dflash/
│   ├── llama.cpp/
│   ├── llama.cpp-phuongncn/
│   ├── keys-vLLm.0.27-Qwen3.8-NVFP4-MTP3-Single-DGX-Spark/
│   ├── TinyZero/
│   ├── vllm-images/
│   └── 各种 *_server.py / *_deploy.sh
├── ai-services/        # AI 服务脚本
│   ├── embedding-server.py
│   ├── llm-api-server.py
│   ├── qwen_server.py
│   ├── nvfp4-api-server.py
│   ├── tts_server.py
│   ├── tts_local_cli.py
│   ├── md2pdf.py
│   ├── download-monitor.py
│   ├── download-progress-server.py
│   ├── ai-stack/
│   ├── finetune-env/
│   ├── llm-env/
│   ├── vllm-env/
│   └── ms-swift-venv/
├── minimax-workspace/  # MiniMax H3 / music3
│   ├── minimax-h3-dgx-spark/
│   ├── minimax-h3-story/
│   ├── minimax-music3-dgx-spark/
│   └── music3-demo/
├── data/               # 数据与知识
│   ├── datasets/
│   ├── papers/
│   ├── academic/
│   ├── CAC2026_ASU_OKC_SFT/
│   ├── okc-sft-training/
│   └── openclaw-backup-*.tar.gz
├── research/           # 研究与实验
│   ├── rl-classic/
│   ├── rl-classic-multialg/
│   ├── rl-deep/
│   ├── rl-demo/
│   ├── rl-env/
│   ├── rl-grpo-env/
│   ├── rl-lab/
│   ├── rl-proto/
│   ├── rl-workspace/
│   ├── ds4/
│   ├── verl-venv/
│   ├── paper-rag-venv/
│   ├── bench/
│   └── nightly/
├── deploy/             # 部署脚本
│   ├── deploy-qwen35b-gguf.sh
│   ├── install-llamafactory.sh
│   ├── resume-dsv4.sh
│   ├── dsv4-ctl.sh
│   └── start-proxy.sh
├── apps/               # 已有，保留
├── code/               # 已有，保留
├── docs/               # 已有，保留
├── infra/              # 已有，保留
├── notes/              # 已有，保留
├── workspace/          # OpenClaw workspace
├── skills/             # 已有
├── bin/                # 已有
├── snap/               # 已有
├── spark/              # 已有
├── sensors/            # 已有
├── archive/            # 已有
├── backup/             # 已有
├── backups/            # 已有
└── [保留原有中文目录] 下载/ 公共/ 图片/ 文档/ 视频/ 音乐/
```

## 归并规则

| 源目录 | 目标目录 | 说明 |
|--------|----------|------|
| nav-server/ | projects/ | 服务导航台 |
| careerflow-agent/ | projects/ | 求职平台 agent |
| repos/llm-tracker/ | projects/llm-tracker | 追踪器 |
| air-separation-project/ | projects/ | 空分项目 |
| airsep-copilot/ | projects/ | 空分 copilot |
| chat-tts-ui/ | projects/ | 对话 TTS 前端 |
| voice-assistant/ | projects/ | 语音助手 |
| postbird/ | projects/ | 项目 |
| xiyangyang/ | projects/ | 项目 |
| verl-agent/ | projects/ | RL agent |
| rl-grpo-air-nl2sql/ | projects/ | RL 项目 |
| openrlhf-project/ | projects/ | RLHF 项目 |
| dsh-plugin-asmemory/ | projects/ | DSH 插件 |
| embedding-docker/ | projects/ | Embedding 服务 |
| mobileforge/ | projects/ | 移动端 |
| graphrag/ | projects/ | GraphRAG |
| knowledge/ | projects/ | 知识库 |
| kg/ | projects/ | 知识图谱 |
| zhishitupu/ | projects/ | 知识图谱 |
| zju-autologin/ | projects/ | 浙大自动登录 |
| zju-web-login/ | projects/ | 浙大登录 |
| napcat-data/ | projects/ | QQ 机器人数据 |
| models/ | models-deploy/ | 模型文件 |
| models-local-qwen38/ | models-deploy/ | 本地 Qwen 模型 |
| qwen38-sglang-deploy/ | models-deploy/ | SGLang 部署 |
| dgx-spark-vllm-dflash/ | models-deploy/ | vLLM 部署 |
| dgx-spark-vllm-qwen3.6-35b-a3b-dflash/ | models-deploy/ | vLLM 部署 |
| llama.cpp/ | models-deploy/ | llama.cpp |
| llama.cpp-phuongncn/ | models-deploy/ | llama.cpp 分支 |
| keys-vLLm.0.27-Qwen3.8-NVFP4-MTP3-Single-DGX-Spark/ | models-deploy/ | vLLM 密钥 |
| TinyZero/ | models-deploy/ | TinyZero |
| vllm_images/ | models-deploy/vllm-images/ | vLLM 镜像 |
| ai-stack/ | ai-services/ | AI 技术栈 |
| finetune-env/ | ai-services/ | 微调环境 |
| llm-env/ | ai-services/ | LLM 环境 |
| vllm-env/ | ai-services/ | vLLM 环境 |
| ms-swift-venv/ | ai-services/ | Swift 环境 |
| verl-venv/ | research/ | RL 环境 |
| paper-rag-venv/ | research/ | 论文 RAG 环境 |
| deepseek-harness/ | projects/ | DeepSeek Harness |
| ds4/ | research/ | DS4 研究 |
| dsask-api/ | projects/ | DS API |
| dsh/ | projects/ | DSH |
| minimax-h3-dgx-spark/ | minimax-workspace/ | MiniMax H3 |
| minimax-h3-story/ | minimax-workspace/ | H3 故事 |
| minimax-music3-dgx-spark/ | minimax-workspace/ | Music3 |
| music3-demo/ | minimax-workspace/ | Music3 演示 |
| datasets/ | data/ | 数据集 |
| papers/ | data/ | 论文 |
| academic/ | data/ | 学术数据 |
| CAC2026_ASU_OKC_SFT/ | data/ | SFT 数据 |
| okc-sft-training/ | research/ | SFT 训练 |
| rl-classic/ | research/ | 经典 RL |
| rl-classic-multialg/ | research/ | 多算法 RL |
| rl-deep/ | research/ | 深度 RL |
| rl-demo/ | research/ | RL 演示 |
| rl-env/ | research/ | RL 环境 |
| rl-grpo-env/ | research/ | GRPO 环境 |
| rl-lab/ | research/ | RL 实验室 |
| rl-proto/ | research/ | RL 原型 |
| rl-workspace/ | research/ | RL 工作区 |
| bench/ | research/ | 基准测试 |
| nightly/ | research/ |  nightly |
| nightly-ml/ | research/ | ML nightly |
| deploy-qwen35b-gguf.sh | deploy/ | 部署脚本 |
| install-llamafactory.sh | deploy/ | 安装脚本 |
| resume-dsv4.sh | deploy/ | DS 脚本 |
| dsv4-ctl.sh | deploy/ | DS 控制 |
| start-proxy.sh | deploy/ | 代理启动 |

## 执行步骤

1. 创建目标目录
2. 移动目录/文件
3. 清理空目录
4. 验证结果

## 经验教训

- 先检查目录是否存在再移动，避免 `mv` 失败导致脚本中断
- 使用 `set -e` 时要注意错误处理
- 后台任务完成后要验证结果
- 保留原始备份，整理前可先创建清单
