---
name: user-research-infrastructure
description: 用户的本地 AI 研究硬件与软件栈：Blackwell GB10 + VLLM + Qwen3.6-35B-A3B-NVFP4 + DeepSeek V4 GGUF + Neo4j
metadata: 
  node_type: memory
  type: project
  originSessionId: 0763b159-87a1-4db6-b891-029e03e3b0cc
---

**硬件**
- 主机：spark-44a8，aarch64 (ARM64)
- CPU：20 核
- 内存：121 GiB（已用 ~92%）
- GPU：**NVIDIA GB10（Blackwell 架构）**，驱动 580.159.03 / CUDA 13.0
- 磁盘：NVMe 3.7 TB（已用 588G，剩余 3.0T）

**本地 AI 服务栈**
- **VLLM EngineCore**（PID 798370，端口 8000）：serving `Qwen3.6-35B-A3B-NVFP4`（压缩张量量化 NVFP4），max-model-len 262144，gpu-memory-utilization 0.88
- **embedding-server**（uvicorn，端口 11434）
- **Neo4j**（Java 进程，~3.2 GiB 内存）
- **openclaw gateway**（Node.js，端口 18789）
- 备选模型：**DeepSeek-V4-Flash-Spark-Mini-Q2-REAP-ds4.gguf**（49GB，本地 benchmark 用）

**Why:** 这些信息直接决定我对用户问题的回答——比如推荐模型时优先选 GB10 能跑的量化版本，不要默认假设 A100/H100。

**How to apply:**
- 提到模型时优先 NVFP4 / GGUF Q2-Q4 量化的本地可选型号
- benchmark/性能讨论时以 GB10 实际表现为锚点
- 提本地已运行服务时先 `lsof -i :端口` 确认端口占用情况再决定能不能复用
- 链接 [[user-research-directions]]、[[user-current-projects]]