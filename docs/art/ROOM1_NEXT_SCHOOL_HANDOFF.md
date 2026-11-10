# 学校交接｜2026-11-11

11 月 10 日收工。明天从**标准休眠楼的候选审图**接着做，先看楼梯间新材质和两款扶手。今天的成果基线是 [GitHub main `eea90b0`](https://github.com/Glandy-T/echoes-of-ruin/commit/eea90b0cfa3c2fe82ec1778618f7feedc26ad30f)。本交接随后单独提交。

## 到学校先打开

1. 在学校副本检查 `git status --short --branch`，再同步 GitHub `main`。如果有同路径的本机差异，先保留并比较，审图以仓库提交为准。
2. 打开[并排审图](experiments/cryo_building_review_v1/preview.md)或[本地 HTML](experiments/cryo_building_review_v1/preview.html)。先看 [A 款扶手](experiments/cryo_building_review_v1/evidence/godot/hr-a_rail.png)和 [B 款扶手](experiments/cryo_building_review_v1/evidence/godot/hr-b_rail.png)，再看[正常视角](experiments/cryo_building_review_v1/evidence/godot/hr-b_occupied.png)与 [28 秒灯光演示](experiments/cryo_building_review_v1/evidence/stair_motion_28s.gif)。
3. 想实机看时，用 Godot 4.6.2 打开 `scenes/dev/cryo_building_review_v1.tscn`，按 **F6**。数字 1–0 依次选 HR、FD、EL、EN、FA 的 A/B，↑↓ 切机位，O 开合门扇，C 切电梯警示，L 切楼梯保底照明。F5 走正式入口。

## 当前结果与下一步

| 项目 | 目前状态 | 接手后的判断 |
|---|---|---|
| ST-01 楼梯墙面与踏面 | 用户确认建筑很少有人走动，环境老化为主。大面已换成既有 PixelLab 细矿物纹理，旧痕集中在贴着踏步与平台的墙脚。主表面实测 80 原生像素／米。 | 用同机位先确认旧痕的位置和明暗。如果还有喷漆感，指出具体一块的位置，按对应的收边、缝隙或环境来源调整。 |
| HR-A/B 扶手 | 两款立柱都落在实际踏面，补了握轨支座。A 为圆管和细竖杆，B 为沿踏步留缝的折板。造型仍待审。 | 先分清问题出在 A/B 的整体轮廓、转角，还是局部比例。当前实测净宽为 **1.616 m／1.617 m**，冻结目标为 **1.80 m**，现阶段只在独立样段比较。要安装时先解决净宽。 |
| FD、EL、EN、FA | 各两款均已出 Godot 实拍。FD/EN 的独立样段验证了闭门阻挡与开后中心通行；EL 警示条可穿过，断电门叶仍挡住角色。FA 是 16F＋B4 外壳候选。 | 各组可独立挑选。FD 落地前复查整扇扫掠；EN 的首层外门位置待确认。FA 正式布光与远景运动采样仍待验证。 |
| 4F v6 与主角 | 4F 镜头、显现触发和强度仍待选。主角 3D 已暂停，身体 v2 保留，最后一版 Tripo 白袍未通过，游戏里继续用纸片占位。 | 先看建筑审图。恢复 4F 或主角时从下方的独立入口接手。 |

**扶手建模的分工建议**。Tripo 可以先试复杂外壳或扶手的新轮廓。扶手定稿要逐级对齐固定点，并在 Blender 中按楼梯尺寸检查净宽与接点。是否更换造型由这轮审图决定。当前两款源文件都在同一个 [Blender 工程](experiments/cryo_building_review_v1/model/interior_accessories.blend)。

**美术约束**。楼内优先表现长期静置的积尘、墙脚与接缝沉积，以及轻微的材质变化。室外痕迹要有暴露位置或滴水来源。Pixel Canals 用作观察参考，PixelLab 负责主体绘画，Aseprite 精修保留分层。最近一次实查 PixelLab 用量为 1994/2000，本轮楼梯两次修订均复用已有贴图。下次真正需要生成时再查账户。[材料与岁月痕迹](cryo_building_production/MATERIALS_AND_AGEING.md) · [生成记录](experiments/cryo_building_review_v1/source/usage_summary.json)

## 复查、旧入口和本机差异

- 审图用独立实时光。已在 Godot 4.6.2 核对同机位画面与楼梯灯光演示，并比对导出模型的贴图密度、握轨坐标和立柱落脚高度。技术核对完成，视觉选择和正式安装仍待定。[审图说明及验证记录](experiments/cryo_building_review_v1/README.md)
- 正式 Room 1、F5 与旧 4F 路线继续沿用各自入口。要看 4F，用 `scenes/dev/cryo_4f_camera_compare_v6.tscn` 按 F6，再按 F8 去走廊。要恢复主角，先读身体和白袍的各自验收状态。[4F v6 审图](experiments/cryo_4f_camera_compare_v6/preview.html) · [身体 v2](experiments/protagonist_tripo_body_v2/preview.html) · [白袍检查](experiments/protagonist_tripo_robe_h31_v1/preview.html)
- 学校机上次使用的 Godot 路径为 `E:/卒業制作/GODOT/Godot_v4.6.2-stable_win64_console.exe`。学校当前安装和项目路径到校后再核对。早期的 4F 操作表、主角诊断和学校工具路径仍可从[11 月 7 日交接归档](https://github.com/Glandy-T/echoes-of-ruin/blob/eea90b0cfa3c2fe82ec1778618f7feedc26ad30f/docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md)查到。上一版楼梯可从 [`f9a3746` 同机位](https://github.com/Glandy-T/echoes-of-ruin/blob/f9a3746c218853eec56d33c441afb6cdc2148acb/docs/art/experiments/cryo_building_review_v1/evidence/godot/hr-a_rail.png)回看。
- 家中有五项交接范围之外的本机差异。学校同步得到的是 GitHub 版本，尤其是 FA-A 应按已发布的候选比较。
  - 已改 `assets/art/cryo_building_review_v1/models/FA-A_complete_envelope.glb` 与 `project.godot`。
  - 未跟踪 `ASSET_CREDITS.md`、`assets/art/room1_integrated_door_v3/room1_integrated_door_v3_door_front.png` 与 `assets/art/room1_open_hero_bake_r1/strip_irradiance.exr`。

给学校 Codex 的简短开场

> 同步 echoes-of-ruin 的 GitHub main，读 `docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md`。先打开最新楼梯审图，和我一起确认低使用频率的旧化以及 A/B 扶手造型。两款均暂在独立样段，安装还要解决净宽。
