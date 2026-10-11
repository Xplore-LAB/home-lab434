# Eval Fixtures

每个 fixture 是一个 `eval/fixtures/<id>.json`，描述一道任务 + 评分标准。

## 字段

- `id`：唯一 ID
- `title`：人读标题
- `source`：上游出处（GitHub URL / 文档锚点）
- `category`：分类（ml-fundamentals / agent-infra / coding / ...）
- `difficulty`：easy / medium / hard
- `expected_max_minutes`：超时阈值
- `spec`：任务规约（语言、允许库、接口、test）
- `rubric`：评分项（name/weight/check）
- `reference`：参考实现路径

## 运行

```bash
python3 eval/run.py fixtures/dl-01-linreg.json
# → { "fixture_id": "...", "score": 0.87, "breakdown": {...}, "duration_s": 142 }
```
