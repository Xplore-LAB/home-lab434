#!/usr/bin/env python3
"""MiMo-V2.6-RL 环境 runner（纯 Docker，绕开 Kubernetes）。

复刻 recipes/general/general_agent 的两容器 pod 拓扑：
  main    — agent 容器，只见 /work/workspace
  sidecar — MCP 工具服务 + verifier，见 /work/system、/work/tools（与 main 共享网络命名空间）

用法:
  python3 mimo_env_runner.py list   [--limit 5]
  python3 mimo_env_runner.py up     --instance <instance_id>
  python3 mimo_env_runner.py ports  --instance <instance_id>
  python3 mimo_env_runner.py verify --instance <instance_id>
  python3 mimo_env_runner.py e2e    --instance <instance_id>
  python3 mimo_env_runner.py down   --instance <instance_id>
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import socket
import subprocess
import sys
import time

TASK_ROOT = pathlib.Path("/home/lab434/datasets/MiMo-V2.6-RL-oss")
GENERAL_ROOT = TASK_ROOT / "general"
PARQUET = GENERAL_ROOT / "train.parquet"
IMAGE_PREFIX = "xiaomimimo/mimo-v2.6-rl-oss"
PREFIX = "mimo"
MCP_CONTAINER = "mimo-mcp-arm"
MCP_TIMEOUT = 300
VERIFY_TIMEOUT = 900
VERIFIER_FILES = ("run_verify.py", "verify.py", "rubrics.json", "answer_key.json",
                  "verifier_meta.json", "_helpers.py")


def sh(cmd, check=True, timeout=None, capture=True):
    p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=capture,
                       text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise SystemExit(f"ERROR: {' '.join(cmd) if isinstance(cmd, list) else cmd}\n"
                         f"exit={p.returncode}\n{(p.stderr or '')[-800:]}")
    return p


def load_rows():
    import pyarrow.parquet as pq
    return pq.read_table(PARQUET).to_pylist()


def find_instance(iid):
    for r in load_rows():
        ei = r.get("extra_info")
        if isinstance(ei, str):
            ei = json.loads(ei)
        ij = ei.get("instance_json") or {}
        if isinstance(ij, str):
            ij = json.loads(ij)
        if ei.get("instance_id") == iid:
            task_dir = ij.get("env_task_dir") or ""
            return {
                "instance_id": iid,
                "dataset_type": ij.get("dataset_type") or ei.get("dataset_type"),
                "docker_image": ij.get("docker_image") or "",
                "task_dir": (GENERAL_ROOT / task_dir).resolve() if task_dir else None,
                "cwd": ij.get("cwd") or "/work/workspace",
                "problem_statement": ij.get("problem_statement") or "",
                "verifier_timeout_sec": ij.get("verifier_timeout_sec"),
            }
    raise SystemExit(f"ERROR: instance not found: {iid}")


def image_ref(docker_image):
    tag = docker_image.split(":")[0]
    return f"{IMAGE_PREFIX}:{tag}"


def manifest(task_dir):
    p = task_dir / "manifest.json"
    if not p.exists():
        raise SystemExit(f"ERROR: manifest.json missing in {task_dir}")
    return json.loads(p.read_text())


def container_names(iid):
    safe = iid.replace("/", "_").lower()
    return f"{PREFIX}-{safe[:28]}-main", f"{PREFIX}-{safe[:28]}-sidecar"


def wait_port(container, port, timeout):
    """在 MCP_CONTAINER 内探测 127.0.0.1:port。

    注意：MCP 服务由原生 arm64 容器 mimo-mcp-arm 提供（见 EXPERIMENT_SOP.md §5），
    不在 main/sidecar 的 netns 里。早期版本探测 main，导致永远探不到、
    每个端口空等 MCP_TIMEOUT 秒。探测目标必须是 mimo-mcp-arm。
    """
    probe = (f"python3 - <<'PY'\n"
             f"import socket,sys\n"
             f"s=socket.socket()\n"
             f"s.settimeout(1)\n"
             f"try:\n"
             f"    s.connect(('127.0.0.1',{port}))\n"
             f"    print('OK')\n"
             f"except Exception as e:\n"
             f"    print('WAIT')\n"
             f"PY")
    deadline = time.time() + timeout
    while time.time() < deadline:
        p = subprocess.run(["docker", "exec", container, "bash", "-lc", probe],
                           capture_output=True, text=True)
        if "OK" in (p.stdout or ""):
            return True
        time.sleep(2)
    return False


def cmd_up(args):
    info = find_instance(args.instance)
    tdir = info["task_dir"]
    if tdir is None or not tdir.exists():
        raise SystemExit(f"ERROR: task dir not found: {tdir}")
    m = manifest(tdir)
    main, side = container_names(args.instance)
    img = image_ref(info["docker_image"])

    print(f"[1/6] instance   : {info['instance_id']}")
    print(f"      image      : {img}")
    print(f"      task_dir   : {tdir}")
    print(f"      cwd        : {info['cwd']}")

    subprocess.run(["docker", "rm", "-f", main, side], capture_output=True, text=True)

    ports = m.get("wait_ports") or []
    print(f"[2/6] 启动 main（拥有网络命名空间）")
    run_main = ["docker", "run", "-d", "--name", main,
                "-v", f"{tdir}/workspace:/work/workspace",
                "-w", info["cwd"]]
    # 不发布 -p p:p：MCP 服务在 mimo-mcp-arm 里，发布这些端口既无意义
    # 又会撞宿主机端口（见 EXPERIMENT_SOP.md §7 故障排查）
    run_main += [img, "sleep", "infinity"]
    sh(run_main)

    print("[3/6] 启动 sidecar（加入 main 的网络命名空间）")
    run_side = ["docker", "run", "-d", "--name", side,
                "--network", f"container:{main}",
                "-v", f"{tdir}/system:/work/system",
                "-v", f"{tdir}/tools:/work/tools",
                img, "sleep", "infinity"]
    sh(run_side)

    print("[4/6] 投放 payload 脚本")
    for f in ("sidecar_entrypoint.py", "mcp_http.py"):
        src = tdir / f
        if src.exists():
            sh(["docker", "exec", side, "mkdir", "-p", "/installed-agent"])
            sh(["docker", "cp", str(src), f"{side}:/installed-agent/{f}"])
    if (tdir / "mcp_bridge.py").exists():
        sh(["docker", "exec", main, "mkdir", "-p", "/work/_setup"])
        sh(["docker", "cp", str(tdir / "mcp_bridge.py"), f"{main}:/work/_setup/mcp_bridge.py"])
    for c in (main, side):
        sh(["docker", "exec", c, "mkdir", "-p", "/logs/verifier"])

    # [5/6] sidecar 不再启动 MCP —— amd64 通用镜像内无 /opt/openai-agents-venv，
    # sidecar_entrypoint.py 必崩（FileNotFoundError）。MCP 由 mimo-mcp-arm 提供。
    print("[5/6] sidecar setup: 跳过（MCP 由 mimo-mcp-arm 提供，见 SOP §5）")

    print(f"[6/6] 等待 MCP 端口（容器 {MCP_CONTAINER}，最多 {MCP_TIMEOUT}s）")
    if not sh(["docker", "inspect", "-f", "{{.State.Running}}", MCP_CONTAINER],
              check=False).stdout.strip() == "true":
        raise SystemExit(
            f"ERROR: MCP 容器 {MCP_CONTAINER} 未运行。"
            f"先按 EXPERIMENT_SOP.md §5 启动它，否则 rollout 无法调用 MCP 工具。")
    ok = True
    for p in ports:
        if wait_port(MCP_CONTAINER, p, MCP_TIMEOUT):
            print(f"      port {p} OK")
        else:
            ok = False
            print(f"      port {p} TIMEOUT")
    log = subprocess.run(["docker", "exec", side, "bash", "-lc",
                          "tail -c 800 /tmp/sidecar_entrypoint.log 2>/dev/null"],
                         capture_output=True, text=True).stdout
    if not ok and log:
        print("--- sidecar log ---")
        print(log)
    print("UP_OK" if ok else "UP_FAILED")
    return 0 if ok else 1


def cmd_ports(args):
    info = find_instance(args.instance)
    m = manifest(info["task_dir"])
    main, side = container_names(args.instance)
    print(f"MCP 容器: {MCP_CONTAINER}")
    for p in (m.get("wait_ports") or []):
        ready = wait_port(MCP_CONTAINER, p, 3)
        print(f"port {p}: {'OK' if ready else 'CLOSED'}")
    return 0


def cmd_verify(args):
    info = find_instance(args.instance)
    tdir = info["task_dir"]
    m = manifest(tdir)
    main, side = container_names(args.instance)
    v = m.get("verifier") or {}
    files = v.get("uploads") or [{"source": f, "target": f"/work/{f}"} for f in VERIFIER_FILES]

    print("[1/3] 上传 verifier 材料到 sidecar")
    for u in files:
        src = tdir / u["source"]
        if src.exists():
            sh(["docker", "cp", str(src), f"{side}:{u['target']}"])
            print(f"      + {u['source']} -> {u['target']}")
    sh(["docker", "exec", side, "mkdir", "-p", "/logs/verifier"])

    cmd = v.get("command") or "python3 /work/run_verify.py"
    timeout = info.get("verifier_timeout_sec") or VERIFY_TIMEOUT
    print(f"[2/3] 运行 verifier: {cmd} (timeout {timeout}s)")
    env_args = []
    for k in ("VERIFY_DETERMINISTIC", "VERIFY_AGENT_JUDGE"):
        env_args += ["-e", f"{k}=1"]
    for k in ("GA_JUDGE_URL", "GA_JUDGE_KEY", "GA_JUDGE_MODEL", "GA_JUDGE_API"):
        import os
        if os.environ.get(k):
            env_args += ["-e", f"{k}={os.environ[k]}"]
    p = subprocess.run(["docker", "exec", *env_args, side, "bash", "-lc", cmd],
                       capture_output=True, text=True, timeout=timeout)
    print("      exit:", p.returncode)
    if p.stdout.strip():
        print("      stdout:", p.stdout.strip()[-1200:])
    if p.stderr.strip():
        print("      stderr:", p.stderr.strip()[-800:])

    print("[3/3] 读取 reward")
    reward_file = v.get("reward_file") or "/logs/verifier/reward.json"
    detail_file = v.get("reward_detail_file") or "/logs/verifier/reward_detail.json"
    for f in (reward_file, detail_file):
        out = subprocess.run(["docker", "exec", side, "bash", "-lc",
                              f"cat {f} 2>/dev/null || echo __MISSING__"],
                             capture_output=True, text=True).stdout.strip()
        print(f"      {f}: {out[:600]}")
    outdir = pathlib.Path(args.outdir or f"/home/lab434/rl-lab/mimo-docker/out/{info['instance_id']}")
    outdir.mkdir(parents=True, exist_ok=True)
    for f in (reward_file, detail_file):
        raw = subprocess.run(["docker", "exec", side, "bash", "-lc", f"cat {f} 2>/dev/null"],
                             capture_output=True, text=True).stdout
        if raw.strip():
            (outdir / pathlib.Path(f).name).write_text(raw)
    print(f"      已保存到 {outdir}")
    return 0


def cmd_down(args):
    main, side = container_names(args.instance)
    subprocess.run(["docker", "rm", "-f", main, side], capture_output=True, text=True)
    print(f"removed {main} {side}")
    return 0


def cmd_list(args):
    n = 0
    for r in load_rows():
        ei = r.get("extra_info")
        if isinstance(ei, str):
            ei = json.loads(ei)
        ij = ei.get("instance_json") or {}
        if isinstance(ij, str):
            ij = json.loads(ij)
        if ij.get("dataset_type") != "general_agent":
            continue
        print(f"{ei.get('instance_id')}\t{ij.get('docker_image')}\t{ij.get('env_task_dir')}")
        n += 1
        if n >= args.limit:
            break
    print(f"({n} shown, 925 total general_agent rows)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "up", "ports", "verify", "e2e", "down"])
    ap.add_argument("--instance")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--outdir")
    a = ap.parse_args()
    if a.cmd == "list":
        return cmd_list(a)
    if not a.instance:
        raise SystemExit("ERROR: --instance required")
    if a.cmd == "up":
        return cmd_up(a)
    if a.cmd == "ports":
        return cmd_ports(a)
    if a.cmd == "verify":
        return cmd_verify(a)
    if a.cmd == "down":
        return cmd_down(a)
    if a.cmd == "e2e":
        rc = cmd_up(a)
        if rc != 0:
            print("e2e: up 失败，跳过 verify")
            return rc
        return cmd_verify(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
