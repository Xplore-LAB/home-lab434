#!/usr/bin/env python3
"""asmemory 读写层：把 DCS 读数写入时序记忆，或生成可复现的模拟工况数据。

零第三方依赖（asmemory 本身只用标准库）。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import random
import sys
import time

DEFAULT_DB = os.environ.get("ASMEMORY_DB_PATH", str(pathlib.Path.home() / ".asmemory" / "airsep-memory.db"))


def load_asmemory():
    """把 asmemory 加进 sys.path 并返回模块。

    查找顺序：
      1. $ASMEMORY_SRC/src
      2. $ASMEMORY_HOME/src
      3. ~/dsh-plugin-asmemory/src
      4. 已安装（直接 import）
    """
    candidates = []
    for env in ("ASMEMORY_SRC", "ASMEMORY_HOME"):
        if os.environ.get(env):
            candidates.append(pathlib.Path(os.environ[env]) / "src")
    candidates.append(pathlib.Path.home() / "dsh-plugin-asmemory" / "src")
    for c in candidates:
        if (c / "asmemory" / "__init__.py").exists():
            sys.path.insert(0, str(c))
            break
    try:
        import asmemory  # noqa: PLC0415

        return asmemory
    except ImportError as e:
        raise SystemExit(
            f"ERROR: 找不到 asmemory 模块（{e}）。\n"
            "  设置 ASMEMORY_HOME=/path/to/dsh-plugin-asmemory，或先安装 asmemory。"
        )


def open_store(db: str):
    am = load_asmemory()
    pathlib.Path(db).parent.mkdir(parents=True, exist_ok=True)
    return am, am.MemoryStore(db)


# ---------------------------------------------------------------- store

def cmd_store(args) -> int:
    am, store = open_store(args.db)
    data = json.loads(pathlib.Path(args.input).read_text())
    readings = data.get("readings") or []
    actions = data.get("actions") or []

    if not readings and not actions:
        print("⚠️  输入里没有 readings / actions，无需写入")
        return 0

    base_ts = args.base_ts if args.base_ts is not None else time.time()
    step = args.step_seconds

    n_s = 0
    for i, r in enumerate(readings):
        ts = r.get("ts")
        if not isinstance(ts, (int, float)):
            ts = base_ts + i * step
        store.add_state(
            am.StateEvent(
                entity=str(r.get("entity") or "unknown").lower(),
                metric=str(r.get("metric") or "value").lower(),
                value=float(r.get("value") or 0.0),
                unit=str(r.get("unit") or ""),
                ts=float(ts),
                tags={"source": data.get("_meta", {}).get("source_image", "unknown")},
            )
        )
        n_s += 1

    n_a = 0
    for i, a in enumerate(actions):
        ts = a.get("ts")
        if not isinstance(ts, (int, float)):
            ts = base_ts + i * step
        store.add_action(
            am.ActionEvent(
                actor=str(a.get("actor") or "operator"),
                verb=str(a.get("verb") or "unknown").lower(),
                object=str(a.get("object") or ""),
                amount=float(a.get("amount") or 0.0),
                ts=float(ts),
            )
        )
        n_a += 1

    print(f"✅ 写入 {n_s} 条状态 + {n_a} 条动作 → {args.db}")
    print(f"   当前记忆库：状态 {store.count_states()} / 动作 {store.count_actions()}")
    store.close()
    return 0


# ---------------------------------------------------------------- simulate

def cmd_simulate(args) -> int:
    """生成可复现的模拟空分工况（用于演示 / 回归测试）。

    ⚠️ 这是**模拟数据**，不是真实工厂数据。演示时必须在 README / 视频中标注。
    """
    am, store = open_store(args.db)
    rng = random.Random(args.seed)
    base_ts = args.base_ts if args.base_ts is not None else time.time() - args.minutes * 60

    limit = 99.5          # 氧纯度法规红线（%）
    guide = 78.0          # 导叶开度初始值
    purity = 99.62

    for i in range(args.minutes):
        ts = base_ts + i * 60
        # 每 20 分钟操作工调一次导叶（保守过量控制：一直开得比需要的多）
        if i > 0 and i % 20 == 0:
            guide = max(55.0, guide - rng.uniform(6.0, 10.0))
            store.add_action(
                am.ActionEvent(actor="operator", verb="valve_adjust", object="guide_vane",
                               amount=round(guide, 1), ts=ts)
            )
        # 纯度向红线缓慢回落（控制系统在收）
        purity += (limit - purity) * 0.06 + rng.gauss(0, 0.012)
        # 注入两次异常工况
        if i in (args.minutes // 2, args.minutes - args.minutes // 5):
            purity -= rng.uniform(0.25, 0.4)
        store.add_state(
            am.StateEvent(entity="oxygen", metric="purity", value=round(purity, 3),
                          unit="%", ts=ts, tags={"source": "simulate", "site": args.site})
        )
        store.add_state(
            am.StateEvent(entity="guide_vane", metric="opening", value=round(guide, 1),
                          unit="%", ts=ts, tags={"source": "simulate"})
        )

    print(f"✅ 模拟 {args.minutes} 分钟工况（seed={args.seed}）→ {args.db}")
    print(f"   状态 {store.count_states()} / 动作 {store.count_actions()}")
    print("   ⚠️  模拟数据，非真实工厂数据")
    store.close()
    return 0


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="asmemory 读写层")
    ap.add_argument("--db", default=DEFAULT_DB, help=f"记忆库路径（默认 {DEFAULT_DB}）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_store = sub.add_parser("store", help="把 dcs_read.py 的输出写入记忆库")
    p_store.add_argument("--in", dest="input", required=True, help="dcs_read.py 输出的 JSON")
    p_store.add_argument("--base-ts", type=float, default=None, help="无时间戳时的基准 unix 时间")
    p_store.add_argument("--step-seconds", type=float, default=60.0, help="无时间戳时的采样间隔")

    p_sim = sub.add_parser("simulate", help="生成可复现的模拟空分工况（演示用）")
    p_sim.add_argument("--minutes", type=int, default=240)
    p_sim.add_argument("--seed", type=int, default=42)
    p_sim.add_argument("--site", default="demo-site")
    p_sim.add_argument("--base-ts", type=float, default=None)

    args = ap.parse_args()
    return {"store": cmd_store, "simulate": cmd_simulate}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
