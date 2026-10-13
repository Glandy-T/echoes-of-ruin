# 主角人体基模试版 v2 — 身体比例待审

2026-10-13。用户选中 pistachio 的 Human Basemeshes 女性基模作为试版起点。
本交付仅用于确认人体比例，不是已经批准的完整角色。头发、长衣、像素贴图尚未制作。

## 当前结果

- 保留作者女性体型、原始形态键值和 A 姿势，仅等比缩放与落地到 1.65 m。
- 基础网格：581 顶点、580 面、1,158 三角面；原始 UV 和 59 骨骨架保留。
- 预览使用一层可关闭、未应用的细分，实际显示 4,636 三角面。
  作者源文件的视口同样使用一层细分；关闭细分的原网格折角明显。
- 纯灰材质，无绘制五官；不以这个灰色指定最终肤色或像素风格。
- 后续头发、长衣须分别制作并保留独立网格和 UV。人体维持连续网格。

## 文件

- `body_165cm_review_v2.blend`：可编辑文件，默认打开三视图预览。
  场景 `01_BODY_MASTER_165cm` 是原始绑定人体；场景 `02_FRONT_SIDE_3QUARTER_REVIEW`
  的三个模型是仅用于展示的静态副本，后续编辑请使用场景 01。
- `evidence/body_165cm_review.png`：实际 Blender 渲染的正面、侧面、三分之四视图。
- `evidence/body_165cm_basecage.png`：关闭细分时的对照；按该版本高度单独缩放为 165 cm。
- `evidence/body_uv.svg`：实际基础网格 UV 线框，未做像素贴图排版优化。
- `evidence/inspection.json`：尺寸、网格、UV、权重覆盖检查结果。
- `evidence/source_inventory.json`：原文件对象和骨架清单。
- `source/`：原始下载包、原始 `.blend` 及当次 GitHub 设定快照。
- `inspect_source.py`、`prepare_review.py`：文件检查和可重复制作脚本。

## 来源与许可

- 作者：**pistachio**。
- 作品：[Human Basemeshes](https://opengameart.org/content/human-basemeshes)。
- 下载：[Human Basemeshes.zip](https://opengameart.org/sites/default/files/Human%20Basemeshes.zip)。
- 作者页面标注：[CC0](https://creativecommons.org/publicdomain/zero/1.0/)。
- 下载日期：2026-10-13。原下载包和原 `.blend` 的 SHA256 记录于 `inspection.json`。
- 作者特别说明该拓扑未充分针对动画优化，主要用于雕刻或进一步拓扑工作。

项目方向已核对 GitHub main `4c201289a5cb1f730897017d2186765f8d1ca470`，
`ART_DIRECTION.md` v0.44 和 `CHARACTER_DESIGN.md`。角色文档仍存在旧像素尺寸，
本试版未将它们采纳为项目技术标准。165 cm、自然比例、无绘制五官、后续长发长衣赤脚，
以当前用户要求为准。

## 检查结果与限制

- 已实际导入 Blender 5.0.1 并完成相机渲染；测得显示人体高约 1.650000 m，足底 Z=0。
- 已重新打开保存的 `.blend`，再次核对尺寸、细分面数、形态键、UV 和骨架关联，结果见
  `evidence/saved_file_validation.json`；可用 `verify_saved.py` 重复检查。
- 基础网格无边界边、非流形边、孤立点或零面积面；全部顶点有骨骼权重。
- 原文件来自旧版 Blender。Blender 5 读取时报告一个失效的孤立形态键
  `KEKey.000` 并自动移除；女性网格实际使用的 `Basis` 和 `Key 1` 保留，
  `Key 1` 继续为作者原值 1.0。原始下载文件不覆盖。
- 原文件的旧视图层影响了依赖图更新；制作脚本将女性网格与骨架链接到新的干净场景。
- 以上是静态文件、几何和覆盖检查，**不是肩、肘、髋、膝变形合格证明**。
- 未制作动画帧，未做动作重定向、Godot 导入或运行测试。
- 当前生产角色、场景和此前被否定的 v1 均未替换。

## 重现

在本目录使用 Blender 5.0.1：

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python .\prepare_review.py
```

脚本仅重建本目录的试版和预览，不覆盖 `source/`。原始包中的嵌入脚本不执行。
