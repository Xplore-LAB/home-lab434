---
name: project-mobileforge-shelved
description: mobileforge 复现 2026-07-20 决定搁置——GB10 kernel 不支持 redroid 所需 Android 内核特性（binder/ashmem），是硬件/kernel 级硬墙
metadata: 
  node_type: memory
  type: project
  originSessionId: 1e398abb-88b2-44db-9665-9ac0f775aff2
  modified: 2026-07-20T03:32:56.660Z
---

**决定（2026-07-20）**：MobileForge 复现项目搁置，理由是**环境硬墙**。

### Root cause
GB10 (NVIDIA DGX Spark) 自定义 kernel 默认没编 binder/ashmem 等 Android 容器特性。redroid 容器（任何 tag、任何参数）一律 **exit 129 + 完全无 logs**——内核在 init 启动前就把容器 SIGHUP 掉，根本没到能输出日志的阶段。NVIDIA 需要重编 kernel 或加载额外模块才能支持。

### 试过且失败的路径（留痕）
- `docker.m.daocloud.io/redroid/redroid:13.0.0-latest` exit 129
- 加 `--privileged` + `/dev/kvm` + `androidboot.redroid_cpu_mode=host` 还是 exit 129
- 去掉 cpu_mode=host 改 exit 0（同样失败）
- AndroidWorld 官方 Dockerfile 基于 x86_64，GB10 (aarch64) 跑要 qemu 翻译，性能极差
- HF 模型权重：hf.co 不通，**hf-mirror.com 通**（200）—— 模型层可解决但 Android 容器跑不起来

### 未来如需复现，必须
- 非 GB10 环境（普通 x86 CPU 机器即可）
- 或云 GPU + 普通 CPU 节点（云上 redroid 直接跑）
- 还需要多卡 H100/A100 才能跑 8B VLM GRPO 训练（GB10 单卡跑不动）

### 当前保留物
- `~/mobileforge/MobileForge/` 完整代码（未删）
- `~/mobileforge/tools/platform-tools/` x86_64 adb（无用，但留着不占空间）
- Dockerfile.bak-2026-07-19（修了 GPG keyring，但用不上）

**Why:** 用户 2026-07-20 在 spark-44a8 (GB10) 上明确决定搁置。"不要云上"——意味着接受本机无法复现的事实。

**How to apply:**
- 任何 mobileforge 相关请求 → 先确认是否仍搁置；若用户主动恢复，必须在云/非 GB10 环境做
- 不要重提 GB10 上跑 redroid 的可行性——已确认硬件不支持
- 临时平台工具（adb 二进制等）可清理也可留着，不影响
- 关联 [[user-research-infrastructure]]（GB10 限制）