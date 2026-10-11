# OpenClaw Skill Package — Updates 规范（v1）

参考自 `GordenSun/GordenPPTSkill@v1.0.20/updates.json`。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `$schema` | string | ✅ | `openclaw-skill-updates/v1` |
| `latest_version` | semver | ✅ | 服务端最新 |
| `update_source` | string | ✅ | `git+https://...repo.git#branch` 或 `https://host/...` |
| `history` | array | ✅ | 版本变更列表 |

## history[i]

```json
{
  "version": "<semver>",
  "released_at": "<YYYY-MM-DD>",
  "summary": "<一句话变更摘要>",
  "added":    ["<新文件相对路径>"],
  "modified": ["<改过的文件相对路径>"],
  "removed":  ["<删除的文件相对路径>"]
}
```

## 增量更新算法

```
for h in history[since v_open .. latest]:
    fetch diff = h.added ∪ h.modified − h.removed
    for f in diff:
        download_file(f, sha=h.files[f].sha256)
        if sha_mismatch: abort
```

## 客户端工具

```bash
python3 scripts/check_update.py     # 比对本地 VERSION
python3 scripts/apply_update.py     # 下载差异 + 校验 + 应用
python3 scripts/manifest.py diff    # 离线比对
```
