---
name: gb10-display-edid-black-screen
description: "GB10 桌面不显示：真因未经证实。已知开机被 systemd.unit=multi-user.target 拦住不进图形栈（2026-09-28 已 set-default 持久化）。原 EDID 死锁说＝推断"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3d855a4f-c6c9-4d17-b25a-83e0e44c4ae1
  modified: 2026-09-28T02:33:10.789Z
---

# GB10 + nvidia-driver-580 桌面黑屏根因

## 现象
- 开机 grub → NVIDIA logo → 短暂画面 → **黑屏 / 显示器无信号**
- `journalctl -k` 反复刷 `nvidia-modeset: WARNING: GPU:0: Unable to read EDID for display device HDMI-0`
- gdm3 service `active (running)` 但 `/var/log/Xorg.0.log` 不存在、X 没起来
- tty1 黑屏无 getty 提示

## 当时的根因推断（⚠️ 2026-09-28 复核：未经证实，见文末）
- GPU：`NVIDIA GB10 (GB20B)` (`lspci` 2e12)，ARM SoC + dGPU 集成架构（GH200/GB10 风格）
- SoC 自带 HDMI PHY，**物理 HDMI 口在板上是 SoC 端的**
- 但 `nvidia_drm` 加载后把 `card1-HDMI-A-1` 挂在 dGPU (card1) 下 → dGPU 试图读 EDID
- dGPU **无真实显示输出硬件** → EDID retry-loop 死锁 → kernel modeset 阶段卡死
- Xorg 起不来、`/sys/module/nvidia_drm/parameters/modeset` 不存在（refcount 0 或命名变）
- gdm 父进程 `active` 但 X 子进程从未产出

## 无效的修复尝试
- ❌ `sudo apt install gdm3 gnome-shell ubuntu-desktop-minimal` — 已经装过（apt "新安装 0 包"）
- ❌ `sudo systemctl start gdm3` — service 起来但 X 不起
- ❌ `/etc/X11/xorg.conf.d/99-nvidia-noedid.conf`:
  ```
  Option "ConnectedMonitor" "DFP-0"
  Option "IgnoreEDID" "true"
  Option "AllowEmptyInitialConfiguration"
  ```
  → **kernel modeset 在 X 之前就 fail，xorg.conf 对它无效**

## 后续方向（待验证）
1. **等 NVIDIA 出支持 SoC 显示路由的驱动版本**（官方 issue tracker）
2. **试 Wayland 路径**（不依赖 kernel modeset）：`WaylandEnable=true` + GNOME Wayland / sway，**待验证**
3. **接受 headless**：x11vnc / wayvnc 远程桌面（这台机器本来就是 AI compute node）
4. **换 BIOS 显示路由**（如果有选项）：把 primary display 指到 SoC 而非 dGPU

## 关键文件位置
- 临时残留：`/etc/X11/xorg.conf.d/99-nvidia-noedid.conf`（已停止 gdm，未删除，待用户手动清）
- 系统日志查询：`journalctl -k | grep -iE 'edid|nvidia-modeset|display'`
- gdm 日志：`/var/log/gdm3/` + `journalctl -u gdm3`

**Why:** 这台机器用户主用 vllm / docker / watchdog，所有服务都跑通，不影响生产力。但"桌面不显示"问题以后还会被反复问。
**How to apply:** 用户再问"桌面不显示" → 先讲下面的"三、已确定的事实"，**不要**把上面的 EDID 死锁说当结论念（它没被证实）。别让 ta 重走 IgnoreEDID。

---

## 一、2026-09-28 复核：原根因链未经证实

当场证据（boot 2026-09-27 11:23，driver `580.159.03`）**不支持**上面的推断：

- 整个 boot 约 6 万行内核日志：`edid` **0 行**、`hung_task|soft lockup|rcu stall|Xid` **0 行**
  → "EDID retry-loop 死锁"零证据
- `card1-Unknown-3` = `connected` + `enabled`，议出真实模式表
  （2560x1440 / 1920x1080×3 / 1280x1440 / 1680x1050）
  → 能拿到这种混杂刷新率清单，说明 **EDID 读得到**，输出硬件是好的
- `[drm] Initialized nvidia-drm 0.0.0 ... on minor 1` + `fb0: nvidia-drmdrmfb`
  → kernel modeset 是**成功**的
- 原文说 `modeset` 参数"不存在"——**实际存在**。但它是 `-r------- root`，
  **非 root 读不到值** → 至今不知道 `modeset=Y` 还是 `N`

**但这不等于原诊断错了。** 这台机器开机根本不进图形栈（见三.1），
失败路径**从未被触发**——"没有证据"≠"证据表明没有"。原调查看到的 EDID 刷屏
无法回看（日志已轮转），也无法复现。

## 二、教训：当时的测试方法无效

原调查手工 `systemctl start gdm3` 造出"gdm active 但 X 不起"，当成驱动理论确证。
但 boot 到 multi-user.target 的系统上手工拉起 gdm3、Xorg 不出画面，
**不能证明切到 graphical.target 后桌面也起不来**。这是把自造状态当成了原始症状。

## 三、已确定的事实

1. **`/proc/cmdline` 有 `systemd.unit=multi-user.target`** —— 用户在 GRUB 菜单按 `e`
   做的一次性覆盖。boot 日志 `Reached target multi-user.target`，之后无 gdm/Xorg 记录。
   `grubenv` 里无 `systemd.unit` → 不持久，重启即消失。
2. **2026-09-28 已持久化命令行启动**：
   `sudo systemctl set-default multi-user.target`
   → `/etc/systemd/system/default.target -> /usr/lib/systemd/system/multi-user.target`
   回退：`sudo systemctl set-default graphical.target`；手动起一次：`sudo systemctl isolate graphical.target`
   ⚠️ cmdline 上只要有 `systemd.unit=`，它就盖过 `default.target`
3. **出厂默认是 Xorg，三层锁死**（NVIDIA DGX Spark 出厂镜像自带，非用户所加）：
   - `/etc/gdm3/custom.conf`: `WaylandEnable=false`（8-16 那次改动只动了自动登录，没碰它）
   - `/usr/lib/udev/rules.d/61-gdm.rules`: DMI=`NVIDIA_DGX_Spark`（非 Dell）
     → `GDM_PREFER_WAYLAND` 不置位 → `gdm_prefer_xorg`
   - 同规则 L80: `ATTR{parameters/modeset}!="Y"` → `gdm_disable_wayland`
   → 原先"试 Wayland 路径"一直没做成，是因为**三道闸都得拆**。而且 Wayland 是
   **偏离出厂默认**的路，出厂把 Xorg 定为默认说明 NVIDIA 认为 Xorg 才是正常路径。
4. **残留 `/etc/X11/xorg.conf.d/99-nvidia-noedid.conf` 仍在**，内含 `IgnoreEDID "true"`。
   在 EDID 可读的情况下这个文件**有害**，试图形前应先删。
5. `gdm3` / `x11vnc.service` 都 `WantedBy=graphical.target`（multi-user 不启动）；
   `x11vnc-gdm-now.service` 是 disabled 的手动助手（起 gdm+x11vnc）。`x11vnc.service` 是 enabled。
6. 这台机器图形栈装的是：GNOME 46 + gdm3 46.2 + ubuntu-desktop（Ubuntu 24.04 默认），另有 xfce4 4.18。
   X11 与 Wayland 会话入口都在 `/usr/share/{xsessions,wayland-sessions}`。

## 四、下一步（未做）

真跑一次 `sudo systemctl isolate graphical.target`，拿 Xorg 的真实报错。
**先删三.4 那个残留文件**。可 SSH 回退 `isolate multi-user.target`，不必重启。
