# OpenClaw Skill Package — Manifest 规范（v1）

参考自 `GordenSun/GordenPPTSkill@v1.0.20/manifest.json`。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `$schema` | string | ✅ | `openclaw-skill-manifest/v1` |
| `skill_name` | string | ✅ | 包名（小写、连字符） |
| `version` | semver | ✅ | 当前版本，例 `1.0.0` |
| `file_count` | int | ✅ | `files` 的 key 数 |
| `files` | object | ✅ | 路径 → FileEntry |

## FileEntry

```json
{
  "sha256": "<hex>",
  "size": <bytes>,
  "version_added": "<semver>",
  "last_modified": "<semver>"
}
```

## 校验工具

```bash
python3 scripts/manifest.py verify manifest.json
python3 scripts/manifest.py diff  manifest.json updates.json
```

## 与上游差异

- 删 `files` 中所有二进制/模板外的依赖项
- 加上 `runtime` 字段（python / node / stdio）
- 加上 `tools_required`（python-pptx、soffice...）
