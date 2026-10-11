# Changelog

按版本倒序列出可读变更。机器读取请用 [`updates.json`](./updates.json)；只读哪些文件变动请用 [`manifest.json`](./manifest.json) 的 `last_modified` 字段。

## 1.0.20 — 2026-06-22

**修复"幽灵图片框"（空 `<a:blip/>`）导致的"无法显示该图片"——这是 1.0.19 漏掉的另一类缺陷。**

- 1.0.19 只修了"能解码失败"的 EMF；但还有一类更隐蔽的：`<p:pic>` 图片框的 `<a:blip/>` 是**空的**（不指向任何图片，slide rels 里也没有对应关系），在所有软件都显示"无法显示该图片"。
- 全库扫描后**统一**把这些空图片框填上占位图（"占位图片 自行替换"），位置/版式/文字不变：
  - `red-teaching-models`：第 1/2/13/18/22/26 页，共 14 处（你反馈的第 1 页 3 张即在此）。
  - `red-teaching-framework`：第 28/29 页，共 6 处。
  - `mckinsey-style`（旧模板）：第 6/7/8 页，共 16 处。
  - `report-massive-reports`（旧模板）：第 90 页，1 处。
- 刷新 `red-teaching-models` 预览（改用第 9/11/12/16 页，避开占位页）；其余模板预览未涉及占位页，保持不变。
- 检测脚本已补强：除"解码失败"外，新增"空 blip"检测，避免再漏。

升级：`python3 scripts/apply_update.py`。

## 1.0.19 — 2026-06-22

**修复 `red-teaching-models` 第 26 页的 4 个 EMF 图标在 Mac PowerPoint / WPS / Keynote 上显示"无法显示该图片"。**

- 该页（铅笔三视角信息图）的 4 个小图标是 Windows EMF 矢量图（`image24~27.emf`），非 Windows 端无法解码，显示为破图框。已统一替换为占位图（"占位图片 自行替换"），其余版式 / 文字 / 配色不变。
- 替换逻辑：只替换被当作"显示主图"（`a:blip`）且无法被解码的图片；艺术效果的 `.wdp` 源层不动。
- 同步刷新 `red-teaching-models` 的 `preview.png`（改用第 2/11/12/16 页，避开占位页）。
- 全库其余 20 套模板经扫描均无此问题；`red-teaching-framework` 不受影响。

升级：`python3 scripts/apply_update.py`。

## 1.0.18 — 2026-06-22

**新增 2 套高级红色教学模板（19 → 21 套）。**

- 新增 `red-teaching-framework`（高级红色教学实施框架，30 页）：满版红色教学图解，完整教学逻辑链（教学整体设计→实施过程→效果评价→反思改进→教学内容图谱），适合教师教学能力比赛 / 说课 / 课程思政。
- 新增 `red-teaching-models`（高级红色数智教学图解，30 页）：同系列图型合辑（漏斗 / 齿轮 / 鱼骨 / 金字塔 / 六边形放射 / 同心圆 / 铅笔信息图 / 雷达），主题偏数智技术与智慧教育，适合按"图型 + 教学环节"挑页。
- 两套均产出完整 `template.pptx + intro.md + detail.json（含 type_scale / 每 slot 容量字段 / page_roles / 每页 use_for）+ preview.png`，单页 1000+ 文本位，是库内信息密度最高的模板。
- **体积优化**：原始 PPT 把照片以无损 PNG（甚至一张 3520×4768、6MB）嵌入，已把不透明照片重编码为 JPEG(q90)、超大透明图降采样并同步更新 rels/内容类型——deck1 26MB→6.4MB（-75%）、deck2 6.7MB→2.4MB（-64%），版式 / 字号 / 配色完全不变。
- `templates/INDEX.md`、`SKILL.md`、`references/original-design-guide.md` 的模板套数同步更新为 21。

升级：`python3 scripts/apply_update.py`。

## 1.0.17 — 2026-06-09

**把"字数限制"从强制改为软性参考，并禁止省略号截断。**

问题：之前为防出框，把"不超 `max_chars`"写得过硬（还建议 `--strict` 出框即拒绝），导致使用 Skill 的 AI 为了凑数**砍掉后半句、在结尾加 `...`**，比轻微超框更难看。

修复：

- **编辑铁律第 3 条重写**：`max_chars`/`chars_per_line`/`max_lines` 改为**软性参考、非硬上限**；略微超出没关系；**严禁为凑数截断文字、加 `...` / `…` / `等等`**；太长应"用更精炼的措辞重写"或"换更大的版式"，实在不行宁可轻微超出�