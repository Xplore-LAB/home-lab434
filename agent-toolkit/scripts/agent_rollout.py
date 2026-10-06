#!/usr/bin/env python3
"""MiMo general_agent 极简 rollout：MiniMax-M3 当策略 + 容器内 bash + MCP 工具。

- 工具 1: bash  → docker exec <main> bash -lc "<cmd>"   (cwd /work/workspace)
- 工具 N: MCP   → docker exec <main> python3 /work/_setup/mcp_bridge.py \
                    --url http://127.0.0.1:<port>/mcp --name <server> --call <tool> --args-json '{...}'
- 结束: 让模型产出最终答案，写入 /work/workspace/answer.md
用法:
  python3 agent_rollout.py --instance s3k_0000_... [--max-steps 24] [--model MiniMax-M3]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import urllib.request

TASK_ROOT = pathlib.Path("/home/lab434/datasets/MiMo-V2.6-RL-oss")
GENERAL_ROOT = TASK_ROOT / "general"
PARQUET = GENERAL_ROOT / "train.parquet"
KEY_FILE = pathlib.Path("/home/lab434/.openclaw/secrets/minimax.key")
JUDGE_URL = "https://api.minimaxi.com/v1/chat/completions"
PREFIX = "mimo"
MCP_CONTAINER = "mimo-mcp-arm"  # 原生 arm64 容器，装 mcp v1，跑 4 个 MCP 工具服务


def sh(cmd, timeout=600):
    return subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout)


def load_instance(iid):
    import pyarrow.parquet as pq
    for r in pq.read_table(PARQUET).to_pylist():
        ei = r.get("extra_info")
        if isinstance(ei, str):
            ei = json.loads(ei)
        ij = ei.get("instance_json") or {}
        if isinstance(ij, str):
            ij = json.loads(ij)
        if ei.get("instance_id") == iid:
            td = ij.get("env_task_dir") or ""
            return {"id": iid, "task_dir": (GENERAL_ROOT / td).resolve(), "cwd": ij.get("cwd") or "/work/workspace",
                    "problem": ij.get("problem_statement") or ""}
    raise SystemExit(f"instance not found: {iid}")


def containers(iid):
    safe = iid.replace("/", "_").lower()[:28]
    return f"{PREFIX}-{safe}-main", f"{PREFIX}-{safe}-sidecar"


def mcp_servers(task_dir):
    m = json.loads((task_dir / "manifest.json").read_text())
    return [(s["name"], s["url"]) for s in (m.get("mcp_servers") or [])]


def bridge(main, url, name, args):
    if args is None:
        cmd = f"python3 /work/_setup/mcp_bridge.py --url {url} --name {name} --list"
    else:
        cmd = (f"python3 /work/_setup/mcp_bridge.py --url {url} --name {name} "
               f"--call {args['tool']} --args-json {json.dumps(args['arguments'], ensure_ascii=False)!r}")
    p = sh(["docker", "exec", MCP_CONTAINER, "bash", "-lc", cmd], timeout=300)
    out = (p.stdout or "") + (p.stderr or "")
    marker = "__MCP_ONESHOT__"
    for line in out.splitlines():
        if marker in line:
            try:
                return json.loads(line.split(marker, 1)[1])
            except Exception:
                return {"raw": line}
    return {"error": out.strip()[-500:]}


def discover_tools(main, servers):
    tools, index = [], []
    for name, url in servers:
        res = bridge(main, url, name, None)
        items = res.get("tools") or (res.get("result") or {}).get("tools") or []
        for t in items:
            tname = t.get("name")
            if not tname:
                continue
            fn = f"{name}__{tname}"
            tools.append({"type": "function", "function": {
                "name": fn,
                "description": (t.get("description") or "")[:900],
                "parameters": t.get("inputSchema") or t.get("input_schema") or {"type": "object", "properties": {}}}})
            index.append({"fn": fn, "server": name, "url": url, "tool": tname})
    return tools, index


def model(messages, tools, model_name, key, max_tokens=2048):
    body = {"model": model_name, "messages": messages, "max_tokens": max_tokens}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    req = urllib.request.Request(JUDGE_URL, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True)
    ap.add_argument("--max-steps", type=int, default=24)
    ap.add_argument("--model", default="MiniMax-M3")
    ap.add_argument("--task-prompt", default=None)
    a = ap.parse_args()

    info = load_instance(a.instance)
    main_c, side_c = containers(a.instance)
    key = KEY_FILE.read_text().strip()
    servers = mcp_servers(info["task_dir"])
    print(f"[rollout] {info['id']}  main={main_c}  mcp_servers={[s[0] for s in servers]}")

    tools, index = discover_tools(main_c, servers)
    print(f"[rollout] 发现 MCP 工具 {len(tools)} 个")

    task = a.task_prompt or info["problem"]
    instr = info["task_dir"] / "instruction.md"
    if instr.exists():
        task = instr.read_text()

    bash_tool = {"type": "function", "function": {
        "name": "bash", "description": "在任务容器里执行 bash 命令（cwd=/work/workspace，可读写工作区）",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}

    sys_prompt = ("你是空分/企业任务的执行 agent。你可以用 bash 查看和修改 /work/workspace，"
                  "也可以用 MCP 工具查询业务系统。完成任务后，把最终答复写入 /work/workspace/answer.md"
                  "（用 bash 的 heredoc 写文件），然后用一句话说明已完成。")
    messages = [{"role": "system", "content": sys_prompt},
                {"role": "user", "content": task}]

    for step in range(1, a.max_steps + 1):
        resp = model(messages, [bash_tool] + tools, a.model, key)
        msg = resp["choices"][0]["message"]
        messages.append(msg)
        tcs = msg.get("tool_calls") or []
        if not tcs:
            print(f"[step {step}] final: {(msg.get('content') or '')[:300]}")
            break
        for tc in tcs:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except Exception:
                args = {}
            if fn == "bash":
                p = sh(["docker", "exec", main_c, "bash", "-lc", args.get("command", "")], timeout=300)
                result = ((p.stdout or "") + (p.stderr or ""))[-4000:]
            else:
                rec = next((x for x in index if x["fn"] == fn), None)
                if not rec:
                    result = f"unknown tool {fn}"
                else:
                    r = bridge(main_c, rec["url"], rec["server"], {"tool": rec["tool"], "arguments": args})
                    result = json.dumps(r, ensure_ascii=False)[:4000]
            print(f"[step {step}] {fn}({str(args)[:120]}) -> {str(result)[:160]}")
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

    chk = sh(["docker", "exec", main_c, "bash", "-lc", "ls -l /work/workspace/answer.md 2>/dev/null || echo NO_ANSWER"])
    print("[rollout] workspace answer.md:", (chk.stdout or "").strip()[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
