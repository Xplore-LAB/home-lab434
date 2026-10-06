#!/usr/bin/env python3
"""MiMo general_agent rollout v2 — MiniMax-M3 策略 + bash + MCP，直指 reward。

v1 教训（2026-09-30 实跑 24 步失败）：
  - bash 结果里混入 `x86_64-binfmt-P: QEMU internal SIGSEGV` 噪声 → agent 以为命令失败、反复重试；
  - 24 步全花在反复 cat 67KB 的 md 上，从没写 answer.md；
  - MiniMax-M3 是推理模型，单步慢，步数预算 = 时间预算。

v2 改动：
  1. NOISE 过滤：bash/MCP 结果里剥掉 qemu/SIGSEGV/Exit 127 噪声行；
  2. max-steps 默认 60，允许中途收敛；
  3. system prompt 直接给出「必答 5 段」模板 + 「前 12 步内必须落 answer.md」的硬约束；
  4. 预置 digest：把 workspace 里已提取的 struct_text.txt（纯文本）作为第一条 user 消息的一部分喂进去，
     避免 agent 反复读原始二进制/docx；digest 也可用 --no-digest 关掉做冷启动对照；
  5. step 14 若 answer.md 还没写，注入 system nudge；
  6. 收尾：answer.md 缺失但模型给了最终文本 → 由脚本兜底写入（verifier 也认 chat 回复，但写文件最稳）。

用法:
  python3 rollout2.py --instance s3k_0000_... [--max-steps 60] [--model MiniMax-M3] [--no-digest]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

TASK_ROOT = pathlib.Path("/home/lab434/datasets/MiMo-V2.6-RL-oss")
GENERAL_ROOT = TASK_ROOT / "general"
PARQUET = GENERAL_ROOT / "train.parquet"
KEY_FILE = pathlib.Path("/home/lab434/.openclaw/secrets/minimax.key")
JUDGE_URL = "https://api.minimaxi.com/v1/chat/completions"
PREFIX = "mimo"
MCP_CONTAINER = "mimo-mcp-arm"

NOISE_RE = re.compile(
    r"(x86_64-binfmt-P.*QEMU|QEMU internal SIGSEGV|Segmentation fault \(core dumped\)|"
    r"^\s*\d+\s+Exit 127\s*$|bash: line \d+:.*Exit 127)", re.M)


def clean(text: str) -> str:
    """剥掉宿主 binfmt/qemu 仿真噪声，避免模型误判命令失败。"""
    return NOISE_RE.sub("", text or "").strip()


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
            return {"id": iid, "task_dir": (GENERAL_ROOT / td).resolve(),
                    "cwd": ij.get("cwd") or "/work/workspace",
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
    out = clean((p.stdout or "") + (p.stderr or ""))
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
                "description": clean((t.get("description") or ""))[:900],
                "parameters": t.get("inputSchema") or t.get("input_schema") or {"type": "object", "properties": {}}}})
            index.append({"fn": fn, "server": name, "url": url, "tool": tname})
    return tools, index


def model(messages, tools, model_name, key, max_tokens=4096):
    body = {"model": model_name, "messages": messages, "max_tokens": max_tokens}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    req = urllib.request.Request(JUDGE_URL, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)


def write_answer(main_c, text):
    """把最终答案写进容器 workspace（answer.md）。"""
    p = subprocess.run(["docker", "exec", "-i", main_c, "bash", "-lc",
                        "cat > /work/workspace/answer.md"],
                       input=text, capture_output=True, text=True, timeout=120)
    return p.returncode == 0


def answer_exists(main_c):
    p = sh(["docker", "exec", main_c, "bash", "-lc",
            "test -s /work/workspace/answer.md && echo YES || echo NO"])
    return "YES" in (p.stdout or "")


SYS = """You are the executing agent for a business closing-readiness task.

HARD RULES (follow exactly):
- Step budget is limited. Do NOT re-read the same file more than once. Do NOT cat the whole
  67KB markdown repeatedly; one pass is enough, prefer python for searching.
- You MUST write /work/workspace/answer.md within your first 12 steps:
    cat > /work/workspace/answer.md << 'EOF'
    <your complete answer in English, with exact dollar amounts and per-item sources>
    EOF
  After the file exists you may still refine it with additional bash/MCP calls, and you MUST
  rewrite the file (same heredoc) with any improvement.
- Do not modify any other file, workspace source documents, or database records.
- Some bash commands print host emulation noise lines (QEMU/SIGSEGV). Those are NOT errors;
  ignore them and rely on the command's real output.
- If a tool result is empty or unclear, do NOT blindly retry the same command: change approach
  (use python3 to parse, or an MCP tool).

REQUIRED ANSWER CONTENT (5 sections, same order):
1. The current recommended transaction and the records excluded from current status.
2. Both documentary-transfer-tax components (county and city) and their approved summary.
3. Every material closing protection with status and relevant amount.
4. A clear ready / not-ready conclusion with reasons.
5. The approved installment payment split and the all-cash direct-sale fallback.
Cite the source document or system for each conclusion in business terms."""

DIGEST_NOTE = """
Below is a plain-text extraction of the task workspace memorandum
(/work/workspace/struct_text.txt). It is the primary evidence for your answer;
you may still query MCP business systems for the DealCloud workspace record."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True)
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument("--model", default="MiniMax-M3")
    ap.add_argument("--no-digest", action="store_true")
    a = ap.parse_args()

    info = load_instance(a.instance)
    main_c, side_c = containers(a.instance)
    key = KEY_FILE.read_text().strip()
    servers = mcp_servers(info["task_dir"])
    print(f"[rollout2] {info['id']}  main={main_c}  mcp_servers={[s[0] for s in servers]}", flush=True)

    tools, index = discover_tools(main_c, servers)
    print(f"[rollout2] 发现 MCP 工具 {len(tools)} 个", flush=True)

    task = a.task_prompt if hasattr(a, "task_prompt") else None
    instr = info["task_dir"] / "instruction.md"
    if instr.exists():
        task = instr.read_text()

    digest = ""
    if not a.no_digest:
        p = sh(["docker", "exec", main_c, "bash", "-lc", "cat /work/workspace/struct_text.txt"])
        digest = clean(p.stdout or "")[:20000]
        print(f"[rollout2] digest seeded: {len(digest)} chars", flush=True)

    bash_tool = {"type": "function", "function": {
        "name": "bash", "description": "Execute a bash command in the task container (cwd=/work/workspace).",
        "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}}

    user_msg = task + ("\n\n" + DIGEST_NOTE + "\n\n" + digest if digest else "")
    messages = [{"role": "system", "content": SYS}, {"role": "user", "content": user_msg}]

    final_text = ""
    for step in range(1, a.max_steps + 1):
        resp = model(messages, [bash_tool] + tools, a.model, key)
        msg = resp["choices"][0]["message"]
        messages.append(msg)
        tcs = msg.get("tool_calls") or []
        if step == 14 and not answer_exists(main_c):
            messages.append({"role": "system", "content":
                             "Reminder: 12 steps used and /work/workspace/answer.md still does not exist. "
                             "Stop investigating and write the file NOW with your best current answer; refine afterwards."})
        if not tcs:
            final_text = msg.get("content") or ""
            print(f"[step {step}] final: {final_text[:300]}", flush=True)
            break
        for tc in tcs:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except Exception:
                args = {}
            if fn == "bash":
                p = sh(["docker", "exec", main_c, "bash", "-lc", args.get("command", "")], timeout=300)
                result = clean((p.stdout or "") + (p.stderr or ""))[-4000:]
            else:
                rec = next((x for x in index if x["fn"] == fn), None)
                if not rec:
                    result = f"unknown tool {fn}"
                else:
                    r = bridge(main_c, rec["url"], rec["server"], {"tool": rec["tool"], "arguments": args})
                    result = json.dumps(r, ensure_ascii=False)[:4000]
            print(f"[step {step}] {fn}({str(args)[:120]}) -> {str(result)[:160]}", flush=True)
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})

    if not answer_exists(main_c):
        src = final_text
        if not src:
            for m in reversed(messages):
                if isinstance(m, dict) and m.get("role") == "assistant" and (m.get("content") or "").strip():
                    src = m["content"]
                    break
        if src:
            ok = write_answer(main_c, src)
            print(f"[rollout2] fallback write answer.md from final chat: {'OK' if ok else 'FAIL'}", flush=True)
    p = sh(["docker", "exec", main_c, "bash", "-lc", "wc -c /work/workspace/answer.md 2>/dev/null || echo MISSING"])
    print("[rollout2] answer.md:", clean(p.stdout or ""), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
