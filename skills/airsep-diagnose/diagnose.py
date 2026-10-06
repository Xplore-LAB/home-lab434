#!/usr/bin/env python3
"""工况诊断：趋势 / 异常 / 因果 / 摘要，输出人读报告。

纯时序数学，不靠 LLM 猜——这是本 Skill 与「让大模型随口分析」的分界线。
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

from memory_io import DEFAULT_DB, open_store


def fmt_ts(ts: float) -> str:
    import datetime

    return datetime.datetime.fromtimestamp(ts).strftime("%m-%d %H:%M")


def cmd_trend(am, store, args) -> int:
    rows = store.query_states(args.entity, args.metric)
    if len(rows) < args.min_points:
        print(f"⚠️  样本不足：{args.entity}.{args.metric} 只有 {len(rows)} 个点"
              f"（需要 ≥{args.min_points}）。先 store 更多数据。")
        return 1
    vals = [r["value"] for r in rows]
    tss = [r["ts"] for r in rows]
    t = am.analysis.trend(vals, tss)
    anoms = am.analysis.detect_anomalies(vals, tss, threshold=args.z)

    print(f"【指标】{args.entity}.{args.metric}  样本 {len(rows)} 点  "
          f"({fmt_ts(tss[0])} → {fmt_ts(tss[-1])})")
    print(f"【数值】最新 {vals[-1]}  均值 {sum(vals)/len(vals):.3f}  "
          f"范围 [{min(vals):.3f}, {max(vals):.3f}]")
    print(f"【趋势】{t.get('direction')}  斜率 {t.get('slope')}")
    print(f"【异常】{len(anoms)} 个离群点 (|z|>{args.z})")
    for a in anoms[: args.max_anomalies]:
        print(f"        {fmt_ts(a['ts'])}  value={a['value']}  z={a['z']}")
    if len(anoms) > args.max_anomalies:
        print(f"        ...还有 {len(anoms) - args.max_anomalies} 个")
    return 0


def cmd_causal(am, store, args) -> int:
    c = am.analysis.causal_effect(store, args.action, args.entity, args.metric,
                                  window=args.window)
    if c.get("delta") is None:
        print(f"⚠️  因果分析数据不足：{args.action} → {args.entity}.{args.metric}"
              f"（动作 {c.get('n_actions', 0)} 次，方向 {c.get('direction')}）")
        return 1
    arrow = "↑" if c["direction"] == "up" else ("↓" if c["direction"] == "down" else "→")
    print(f"【因果】{args.action} → {args.entity}.{args.metric}")
    print(f"        {c['before_mean']} → {c['after_mean']}  "
          f"(Δ={c['delta']}, {arrow} {c['direction']})  基于 {c['n_actions']} 次动作")
    return 0


def cmd_summary(am, store, args) -> int:
    s = am.analysis.summary(store)
    print("【记忆库摘要】")
    print(json.dumps(s, ensure_ascii=False, indent=2))
    return 0


def cmd_export(am, store, args) -> int:
    try:
        out = am.export.export_datalens(
            store,
            indicator_entity=args.entity,
            indicator_metric=args.metric,
            control_verb=args.action,
            regulatory_limit=args.limit,
            indicator_name=args.indicator_name or args.metric,
            indicator_unit=args.unit,
            control_name=args.control_name or args.action,
            control_unit=args.control_unit,
            site_name=args.site,
        )
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  导出失败：{e}")
        return 1

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    csv_p = outdir / "airsep_datalens.csv"
    cfg_p = outdir / "airsep_datalens.config.json"
    csv_p.write_text(out["csv"])
    cfg_p.write_text(json.dumps(out["config"], ensure_ascii=False, indent=2))
    print("✅ DataLens 导出完成")
    print(f"   CSV    → {csv_p}")
    print(f"   config → {cfg_p}")
    print(f"   下一步：用 DataLens 打开 CSV + 加载 config，查看「安全区内的过量控制」节能空间")
    return 0


def cmd_report(am, store, args) -> int:
    """端到端诊断报告：趋势 + 异常 + 因果 + 节能空间估计。"""
    rows = store.query_states(args.entity, args.metric)
    if len(rows) < args.min_points:
        print(f"⚠️  样本不足（{len(rows)} < {args.min_points}），无法生成报告")
        return 1
    vals = [r["value"] for r in rows]
    tss = [r["ts"] for r in rows]
    t = am.analysis.trend(vals, tss)
    anoms = am.analysis.detect_anomalies(vals, tss, threshold=args.z)
    c = am.analysis.causal_effect(store, args.action, args.entity, args.metric,
                                  window=args.window)

    head = "=" * 58
    print(head)
    print(f"  空分装置工况诊断报告 — {args.entity}.{args.metric}")
    print(head)
    print(f"样本区间   {fmt_ts(tss[0])} → {fmt_ts(tss[-1])}   共 {len(rows)} 点")
    print(f"当前值     {vals[-1]}   均值 {sum(vals)/len(vals):.3f}")
    print(f"趋势       {t.get('direction')}（斜率 {t.get('slope')}）")
    print(f"异常点     {len(anoms)} 个")
    for a in anoms[: args.max_anomalies]:
        print(f"           · {fmt_ts(a['ts'])}  value={a['value']}  z={a['z']}")

    if c.get("delta") is not None:
        arrow = "↑" if c["direction"] == "up" else ("↓" if c["direction"] == "down" else "→")
        print(f"因果       {args.action} → {args.metric}: "
              f"{c['before_mean']} → {c['after_mean']} (Δ={c['delta']} {arrow})")
    else:
        print(f"因果       数据不足（动作 {c.get('n_actions', 0)} 次）")

    # 节能空间：指标高于红线时的"安全裕度"（保守估计）
    limit = args.limit
    above = [v for v in vals if v > limit]
    if above:
        margin = sum(above) / len(above) - limit
        print(f"节能空间   均值超红线 {margin:.3f}{args.unit or ''}，"
              f"{(len(above)/len(vals)*100):.0f}% 的时间存在可压缩裕度")
        print(f"           → 可用 DataLens 量化（analyze --export）")
    else:
        print("节能空间   未检出超红线区间")
    print(head)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="空分装置工况诊断")
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--entity", default="oxygen")
    ap.add_argument("--metric", default="purity")
    ap.add_argument("--action", default="valve_adjust")
    ap.add_argument("--limit", type=float, default=99.5, help="法规红线")
    ap.add_argument("--unit", default="%")
    ap.add_argument("--z", type=float, default=2.0, help="异常检测 z 阈值")
    ap.add_argument("--window", type=float, default=1800.0, help="因果分析窗口（秒）")
    ap.add_argument("--min-points", type=int, default=10)
    ap.add_argument("--max-anomalies", type=int, default=5)

    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("trend")
    sub.add_parser("causal")
    sub.add_parser("summary")
    sub.add_parser("report")

    p_exp = sub.add_parser("export", help="导出 DataLens 格式 CSV + config")
    p_exp.add_argument("--outdir", default="./out")
    p_exp.add_argument("--indicator-name", default=None)
    p_exp.add_argument("--control-name", default=None)
    p_exp.add_argument("--control-unit", default="%")
    p_exp.add_argument("--site", default="")

    args = ap.parse_args()
    am, store = open_store(args.db)
    try:
        fn = {"trend": cmd_trend, "causal": cmd_causal, "summary": cmd_summary,
              "export": cmd_export, "report": cmd_report}[args.cmd]
        return fn(am, store, args)
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
