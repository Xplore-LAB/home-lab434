---
name: gorden-ppt-skill
description: 用 21 套内置中文 PPT 模板生成/编辑 .pptx，只换文字不破坏版式。底层调上游 GordenSun/GordenPPTSkill 的 build_pptx.py。
---

# gorden-ppt-skill (OpenClaw wrapper)

> 上游仓库：`https://github.com/GordenSun/GordenPPTSkill` (v1.0.20)
> 本 skill 是上游的薄包装，所有能力在 `scripts/`、`templates/`、`manifest.json`。

## 何时启用

用户说"做 / 生成 / 制作 / 编辑一份 PPT / 演示文稿 / .pptx"。

## 第一步：拉更新

```bash
python3 scripts/apply_update.py
```

## 工作流（5 步）

1. 读 `templates/<slug>/detail.json`，了解每页文本槽
2. 选页 → 写 `edits.json`
3. 跑：
   ```bash
   python3 scripts/build_pptx.py \
       templates/template.pptx \
       edits.json \
       out/final.pptx \
       --detail templates/detail.json \
       --no-lint
   ```
4. （可选）渲染预览：
   ```bash
   python3 scripts/render_slides.py out/final.pptx out/preview
   ```
5. 把 `out/final.pptx` 给用户

## 依赖

```bash
python3 -m pip install python-pptx
# soffice (libreoffice), pdftoppm (poppler) — 系统包
```

## 许可

上游仓库仅限**个人学习与研究**，严禁商业用途。
