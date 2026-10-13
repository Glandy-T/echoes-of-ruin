# 主角人体基模 v2.1：权重修复与局部验证

2026-10-13。基于用户选择的 pistachio Human Basemeshes 女性基模 v2。
这不是已通过全部动画测试的成品角色，也不包含被用户否定的自建头发和白袍。

## 修复范围

- 原文件保留于相邻 `player_basemesh_v2`，本次保存为新 `.blend`。
- 将没有对应骨骼的 `heel.L/R` 权重合并进同侧 `foot.L/R`。
- 每个顶点保留最强四个有效骨骼影响并归一化。
- 保留原始 UV、形态键 `Key 1 = 1.0`、体型与 1.65 m 评估高度。
- 文件只保留实际绑定人体主场景，去掉 v2 中仅展示用途的静态三视图场景。

## 已确认和未解决的问题

| 项目 | 修复前 | 修复后 |
| --- | ---: | ---: |
| 没有对应变形骨骼的顶点组 | 2 | 0 |
| 超过四个骨骼影响的顶点 | 14 | 0 |
| 权重未归一化的顶点 | 96 | 0 |
| 无有效骨骼权重的顶点 | 0 | 0 |

UV 检测没有零面积三角形、超出 0–1 的三角形或完全相同的叠放三角形，
但检出 **48 对局部重叠**，其中 38 对不共享网格顶点，34 对不共享顶点且重叠面积大于 `1e-7`。
这些计数是三角形对数，不是 UV 岛数量。躯干和脚趾附近存在实际重叠，不能称为可直接绘制最终贴图。
本轮保留 UV，**在最终人体像素贴图绘制前需要修复**。重叠总面积为逐对累计值，不代表唯一覆盖面积。

姿态图片仅用于有限关节诊断。它们不证明完整动作、动作重定向、衣发穿插或 Godot 运行通过。
原作者已说明该拓扑并非充分针对动画优化；最终动作可能仍需局部拓扑与权重调整。

## 文件与重现

- `body_165cm_validated_v2_1.blend`：可编辑的中立姿态人体与原始骨架。
- `repair_weights.py` / `repair_report.json`：修复脚本和修复前后指标。
- `validate_v2_1.py` / `validation_report.json`：重新打开文件后的 UV、骨架与姿态诊断。
- `pose_rest.png`、`pose_shoulder_elbow.png`、`pose_hip_knee.png`：实际 Blender 渲染。

在 Blender 5.0.1 中依次以 `--background --factory-startup --disable-autoexec --python-exit-code 1 --python` 执行
`repair_weights.py` 和 `validate_v2_1.py`。前者需相邻 v2 文件，后者读取本目录的 v2.1 文件。
诊断姿态不写入保存的 `.blend`。

## 来源

作者 **pistachio**，作品 [Human Basemeshes](https://opengameart.org/content/human-basemeshes)，作者页面标注 CC0。
原始压缩包、原 `.blend`、来源哈希及 1.65 m 制作脚本保存在相邻 `player_basemesh_v2`。
本轮衣发素材选择记录见 `docs/art/CHARACTER_ASSET_SOURCING_20261013.md`。
