#!/usr/bin/env python3
"""MiMo-V2.6-RL-oss 实验运行工具包

Usage:
  python3 run_experiments.py smoke-test --instance <IID>
  python3 run_experiments.py batch --instances <IID1> <IID2> ...
  python3 run_experiments.py analyze --results <out_dir>

Research value:
  - Q1: 不同任务类型的 RL 迁移效果（general vs terminal）
  - Q2: Evidence grounding 要求对 agent 行为的影响
  - Q3: Reward hacking 防护的有效性
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE = Path("/home/lab434/research/rl-lab/mimo-docker")
OUT = BASE / "out"
LOGS = BASE / "logs"


def cmd_smoke_test(args: argparse.Namespace) -> int:
    """单任务 smoke test：up → ports → e2e → reward"""
    iid = args.instance
    print(f"[smoke-test] instance={iid}")
    
    # 1. up
    print("[smoke-test] step 1/4: up")
    p = subprocess.run(
        [sys.executable, str(BASE / "mimo_env_runner.py"), "up", "--instance", iid],
        capture_output=True, text=True, timeout=600
    )
    if p.returncode != 0:
        print("UP FAILED:", p.stderr[-500:])
        return 1
    print(p.stdout[-300:])
    
    # 2. ports
    print("[smoke-test] step 2/4: ports")
    p = subprocess.run(
        [sys.executable, str(BASE / "mimo_env_runner.py"), "ports", "--instance", iid],
        capture_output=True, text=True, timeout=120
    )
    print(p.stdout[-300:])
    
    # 3. e2e (rollout)
    print("[smoke-test] step 3/4: rollout")
    rollout_log = LOGS / f"{iid}-rollout.log"
    rollout_cmd = [
        sys.executable, str(BASE / "rollout2.py"),
        "--instance", iid,
        "--max-steps", str(args.max_steps),
        "--model", args.model,
    ]
    with open(rollout_log, "w") as f:
        p = subprocess.run(
            rollout_cmd,
            stdout=f, stderr=subprocess.STDOUT,
            timeout=args.rollout_timeout
        )
    print(f"rollout exit={p.returncode}, log={rollout_log}")
    
    # 4. verify
    print("[smoke-test] step 4/4: verify")
    env = {
        "GA_JUDGE_URL": "https://api.minimaxi.com/v1",
        "GA_JUDGE_KEY": Path("/home/lab434/.openclaw/secrets/minimax.key").read_text().strip(),
        "GA_JUDGE_MODEL": "MiniMax-M3",
        "GA_JUDGE_API": "chat",
        "VERIFY_DETERMINISTIC": "1",
        "VERIFY_AGENT_JUDGE": "1",
    }
    verify_dir = OUT / iid
    verify_dir.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(
        [sys.executable, str(BASE / "mimo_env_runner.py"), "verify", "--instance", iid],
        env={**__import__('os').environ, **env},
        capture_output=True, text=True, timeout=900
    )
    print(p.stdout[-500:])
    if p.stderr:
        print("STDERR:", p.stderr[-200:])
    
    # 5. 收集结果
    reward_file = verify_dir / "reward.json"
    detail_file = verify_dir / "reward_detail.json"
    result = {
        "instance_id": iid,
        "model": args.model,
        "max_steps": args.max_steps,
        "reward": None,
        "detail": None,
    }
    if reward_file.exists():
        result["reward"] = json.loads(reward_file.read_text())
    if detail_file.exists():
        result["detail"] = json.loads(detail_file.read_text())
    
    # 保存实验记录
    record = verify_dir / "experiment_record.json"
    record.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n[smoke-test] result: {json.dumps(result, indent=2)}")
    
    # 6. down
    print("[smoke-test] cleanup: down")
    subprocess.run(
        [sys.executable, str(BASE / "mimo_env_runner.py"), "down", "--instance", iid],
        capture_output=True, timeout=120
    )
    
    return 0 if result.get("reward", {}).get("reward") == 1.0 else 2


def cmd_batch(args: argparse.Namespace) -> int:
    """批量运行多个 instance"""
    instances = args.instances or []
    if not instances:
        print("No instances specified")
        return 1
    
    results = []
    for iid in instances:
        print(f"\n{'='*60}")
        print(f"[batch] Running {iid}")
        print(f"{'='*60}")
        try:
            # 简化版：只做 verify（假设环境已就绪）
            env = {
                "GA_JUDGE_URL": "https://api.minimaxi.com/v1",
                "GA_JUDGE_KEY": Path("/home/lab434/.openclaw/secrets/minimax.key").read_text().strip(),
                "GA_JUDGE_MODEL": "MiniMax-M3",
                "GA_JUDGE_API": "chat",
                "VERIFY_DETERMINISTIC": "1",
                "VERIFY_AGENT_JUDGE": "1",
            }
            p = subprocess.run(
                [sys.executable, str(BASE / "mimo_env_runner.py"), "verify", "--instance", iid],
                env={**__import__('os').environ, **env},
                capture_output=True, text=True, timeout=900
            )
            reward_file = OUT / iid / "reward.json"
            reward = json.loads(reward_file.read_text()) if reward_file.exists() else None
            results.append({
                "instance_id": iid,
                "reward": reward,
                "stdout": p.stdout[-200:],
                "stderr": p.stderr[-200:] if p.stderr else "",
            })
        except Exception as e:
            results.append({
                "instance_id": iid,
                "error": str(e),
            })
    
    # 保存 batch 结果
    batch_file = OUT / f"batch-{__import__('datetime').datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    batch_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n[batch] results saved to {batch_file}")
    
    # 统计
    rewards = [r.get("reward", {}).get("reward") for r in results if r.get("reward")]
    if rewards:
        print(f"[batch] pass_rate: {sum(1 for r in rewards if r == 1.0)}/{len(rewards)} = {sum(rewards)/len(rewards):.2f}")
    
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """分析实验结果"""
    results_dir = Path(args.results or OUT)
    print(f"[analyze] scanning {results_dir}")
    
    records = []
    for f in results_dir.rglob("experiment_record.json"):
        try:
            records.append(json.loads(f.read_text()))
        except Exception:
            pass
    
    if not records:
        print("No experiment records found")
        return 1
    
    print(f"[analyze] found {len(records)} records")
    rewards = [r.get("reward", {}).get("reward") for r in records if r.get("reward")]
    if rewards:
        print(f"  pass_rate: {sum(1 for r in rewards if r == 1.0)}/{len(rewards)}")
        print(f"  mean reward: {sum(rewards)/len(rewards):.3f}")
    
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="MiMo-V2.6-RL-oss 实验工具包")
    sub = parser.add_subparsers(dest="command")
    
    # smoke-test
    p1 = sub.add_parser("smoke-test", help="单任务完整流程")
    p1.add_argument("--instance", required=True, help="Instance ID")
    p1.add_argument("--model", default="MiniMax-M3", help="Policy model")
    p1.add_argument("--max-steps", type=int, default=60, help="Max rollout steps")
    p1.add_argument("--rollout-timeout", type=int, default=1800, help="Rollout timeout (s)")
    
    # batch
    p2 = sub.add_parser("batch", help="批量 verify（假设环境已就绪）")
    p2.add_argument("--instances", nargs="+", help="Instance IDs")
    
    # analyze
    p3 = sub.add_parser("analyze", help="分析实验结果")
    p3.add_argument("--results", help="Results directory")
    
    args = parser.parse_args()
    if args.command == "smoke-test":
        return cmd_smoke_test(args)
    elif args.command == "batch":
        return cmd_batch(args)
    elif args.command == "analyze":
        return cmd_analyze(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
