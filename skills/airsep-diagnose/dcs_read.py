#!/usr/bin/env python3
"""DCS 截图 → 结构化工艺数据（StepFun 视觉）。

零第三方依赖：只用标准库 + urllib。
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

STEPFUN_BASE = os.environ.get("STEPFUN_OPENAI_BASE", "https://api.stepfun.com/step_plan/v1")
STEPFUN_MODEL = os.environ.get("STEPFUN_MODEL", "step-3.7-flash")

# ⚠️ step-3.7-flash 是推理模型：思考写在 reasoning_content，content 可能为空。
# max_tokens 给太小 → 思考吃光预算 → content 变空字符串。必须给足。
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4096"))

PROMPT = """你是空分装置（air separation unit）的工艺助理。请阅读这张 DCS 截图 / 现场仪表照片，抽取所有可读的工艺参数。

只输出 JSON，不要任何解释、不要 markdown 代码围栏。格式：

{
  "readings": [
    {"ts": "HH:MM 或截图上的时间，读不到就填 null",
     "entity": "设备/位号英文小写，如 oxygen / nitrogen / argon / column",
     "metric": "指标英文小写，如 purity / pressure / level / flow / temperature",
     "value": 99.2,
     "unit": "% 或截图上的单位",
     "raw_label": "截图上的原始文字"}
  ],
  "actions": [
    {"actor": "operator 或 dcs",
     "verb": "动作英文小写，如 valve_adjust / setpoint_change",
     "object": "被操作对象英文小写，如 guide_vane / reflux_valve",
     "amount": 68.0,
     "unit": "%"}
  ],
  "confidence": 0.0 到 1.0 之间的数字，表示你对自己读数的把握,
  "notes": "读不清的地方说明"
}

规则：
- 读不出的字段填 null，不要编造数值。
- 截图里若是纯文字列表（如 O2=99.2% / Valve=68%），按规则映射到 entity/metric/action。
- 一个字都读不出来时，readings 和 actions 都返回空数组，并在 notes 说明。
"""


def load_api_key() -> str:
    key = os.environ.get("STEPFUN_API_KEY", "").strip()
    if key:
        return key
    for p in (
        pathlib.Path.home() / ".openclaw" / "secrets" / "stepfun.key",
        pathlib.Path.home() / ".openclaw" / "secrets" / "stepfun.env",
    ):
        if p.exists():
            text = p.read_text().strip()
            m = re.search(r"STEPFUN_API_KEY=(.+)", text)
            if m:
                return m.group(1).strip()
            if text and "\n" not in text:
                return text
    raise SystemExit("ERROR: 找不到 StepFun API Key（设置 STEPFUN_API_KEY 或写入 ~/.openclaw/secrets/stepfun.key）")


def call_vision(image_path: pathlib.Path, api_key: str, max_tokens: int) -> dict:
    if not image_path.exists():
        raise SystemExit(f"ERROR: 图片不存在: {image_path}")
    b64 = base64.b64encode(image_path.read_bytes()).decode()
    ext = image_path.suffix.lstrip(".").lower() or "png"
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "png")

    body = {
        "model": STEPFUN_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
                ],
            }
        ],
    }
    req = urllib.request.Request(
        STEPFUN_BASE + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        raise SystemExit(f"ERROR: StepFun HTTP {e.code}: {detail}")
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"ERROR: 调用 StepFun 失败: {e}")

    choice = resp.get("choices", [{}])[0]
    msg = choice.get("message", {}) or {}
    content = (msg.get("content") or "").strip()
    reasoning = (msg.get("reasoning_content") or msg.get("reasoning") or "")

    if not content:
        raise SystemExit(
            "ERROR: 模型 content 为空（推理模型吃光 token）。\n"
            f"  finish_reason={choice.get('finish_reason')} "
            f"completion_tokens={resp.get('usage', {}).get('completion_tokens')}\n"
            f"  对策：提高 MAX_TOKENS（当前 {max_tokens}）后重试。\n"
            f"  reasoning 前 200 字：{reasoning[:200]}"
        )

    return {"content": content, "reasoning": reasoning, "usage": resp.get("usage", {})}


def parse_payload(content: str) -> dict:
    """从模型输出里抠出 JSON（容忍 ```json 围栏 / 前后废话）。"""
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 退化：抓第一个平衡的 {...}
    start = text.find("{")
    if start >= 0:
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
    raise SystemExit(f"ERROR: 模型没输出合法 JSON。原始输出前 400 字：\n{content[:400]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="DCS 截图 → 结构化工艺数据（StepFun 视觉）")
    ap.add_argument("--image", required=True, help="DCS 截图路径")
    ap.add_argument("--out", help="输出 JSON 路径（默认打印到 stdout）")
    ap.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    ap.add_argument("--keep-reasoning", action="store_true", help="把模型 reasoning 也写进输出（调试用）")
    args = ap.parse_args()

    api_key = load_api_key()
    out = call_vision(pathlib.Path(args.image), api_key, args.max_tokens)
    payload = parse_payload(out["content"])

    payload.setdefault("readings", [])
    payload.setdefault("actions", [])
    payload.setdefault("confidence", None)
    payload.setdefault("notes", "")
    payload["_meta"] = {
        "model": STEPFUN_MODEL,
        "source_image": str(pathlib.Path(args.image).resolve()),
        "usage": out["usage"],
    }
    if args.keep_reasoning:
        payload["_meta"]["reasoning"] = out["reasoning"]

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(args.out).write_text(text)
        print(
            f"✅ 读出 {len(payload['readings'])} 个读数 / {len(payload['actions'])} 个动作 "
            f"→ {args.out}  (confidence={payload['confidence']})"
        )
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
