# 继续制作交接｜2026-11-15

11 月 15 日已沿用户认可的 C 轮廓完成[一体化护栏完整双跑候选](experiments/cryo_handrail_full_v1/preview.md)：两跑、转台、上下平台、墙内握槽及 PixelLab 像素表面。保留原踏步、平台和 L01 灯条几何，Godot 两跑及转台实测净宽约 **1.80 m**。本轮完整接合与材质待审，正式场景尚未替换；[原单段灰模](experiments/cryo_handrail_integrated_v1/preview.md)继续保留作造型基线。

## 继续时先打开

1. 在学校副本检查 `git status --short --branch`，再同步 GitHub `main`。如果有同路径的本机差异，先保留并比较，审图以仓库提交为准。
2. 打开[完整 C 对比](experiments/cryo_handrail_full_v1/preview.md)或[本地 HTML](experiments/cryo_handrail_full_v1/preview.html)，先看双跑整体、握槽及折返。每组为本轮同机位灰模／像素表面。其他建筑候选继续从[原并排审图](experiments/cryo_building_review_v1/preview.md)查看。
3. 用 Godot 4.6.2 打开 `scenes/dev/cryo_handrail_full_v1.tscn` 按 **F6**。↑↓ 切机位、G 切灰模／像素、空格暂停演示、L 演示灯光故障。其他建筑候选入口为 `scenes/dev/cryo_building_review_v1.tscn`。

## 当前结果与下一步

| 项目 | 目前状态 | 接手后的判断 |
|---|---|---|
| ST-01 楼梯墙面与踏面 | 用户确认建筑很少有人走动，环境老化为主。大面已换成既有 PixelLab 细矿物纹理，旧痕集中在贴着踏步与平台的墙脚。主表面实测 80 原生像素／米。 | 用同机位先确认旧痕的位置和明暗。如果还有喷漆感，指出具体一块的位置，按对应的收边、缝隙或环境来源调整。 |
| HR-C 一体化扶手 | 单段轮廓已认可，完整双跑候选已交付；墙侧握槽为真实凹腔，实际有效深度约 65 mm。新 C 表面由 PixelLab 生成，分层源和额度记录已保存。 | 先审本轮完整效果；通过后再安装至实际楼梯间，结合游戏镜头、移动控制器及门的扫掠验证。 |
| FD、EL、EN、FA | 各两款均已出 Godot 实拍。FD/EN 的独立样段验证了闭门阻挡与开后中心通行；EL 警示条可穿过，断电门叶仍挡住角色。FA 是 16F＋B4 外壳候选。 | 各组可独立挑选。FD 落地前复查整扇扫掠；EN 的首层外门位置待确认。FA 正式布光与远景运动采样仍待验证。 |
| 4F v6 与主角 | 4F 镜头、显现触发和强度仍待选。主角 3D 已暂停，身体 v2 保留，最后一版 Tripo 白袍未通过，游戏里继续用纸片占位。 | 先看建筑审图。恢复 4F 或主角时从下方的独立入口接手。 |

**扶手当前交付**。[完整 Blender](experiments/cryo_handrail_full_v1/model/handrail_full_v1.blend)、GLB、分层 Aseprite、12 组同机位对照和 28 秒灯光演示均见[说明](experiments/cryo_handrail_full_v1/README.md)。净宽射线与静态胶囊通过不等于碰撞爬楼控制器已完成。原 A/B 和单段 C 只供追溯。

**美术约束**。楼内优先表现长期静置的环境变化，避免人为踩踏和喷漆式污斑。Pixel Canals 用作观察参考，PixelLab 负责主体绘画，Aseprite 精修保留分层。11 月 15 日已核实账户重置：本轮新图消耗 9／2,000，剩 1,991，网页显示下次重置／续费为 12 月 13 日。旧的 1994／2000 属上一期。[本轮生成记录](experiments/cryo_handrail_full_v1/source/generation_record.json) · [材料与岁月痕迹](cryo_building_production/MATERIALS_AND_AGEING.md)

## 复查、旧入口和本机差异

- 审图用独立实时光。已在 Godot 4.6.2 核对同机位画面与楼梯灯光演示，并比对导出模型的贴图密度、握轨坐标和立柱落脚高度。技术核对完成，视觉选择和正式安装仍待定。[审图说明及验证记录](experiments/cryo_building_review_v1/README.md)
- 正式 Room 1、F5 与旧 4F 路线继续沿用各自入口。要看 4F，用 `scenes/dev/cryo_4f_camera_compare_v6.tscn` 按 F6，再按 F8 去走廊。要恢复主角，先读身体和白袍的各自验收状态。[4F v6 审图](experiments/cryo_4f_camera_compare_v6/preview.html) · [身体 v2](experiments/protagonist_tripo_body_v2/preview.html) · [白袍检查](experiments/protagonist_tripo_robe_h31_v1/preview.html)
- 学校机上次使用的 Godot 路径为 `E:/卒業制作/GODOT/Godot_v4.6.2-stable_win64_console.exe`。学校当前安装和项目路径到校后再核对。早期的 4F 操作表、主角诊断和学校工具路径仍可从[11 月 7 日交接归档](https://github.com/Glandy-T/echoes-of-ruin/blob/eea90b0cfa3c2fe82ec1778618f7feedc26ad30f/docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md)查到。上一版楼梯可从 [`f9a3746` 同机位](https://github.com/Glandy-T/echoes-of-ruin/blob/f9a3746c218853eec56d33c441afb6cdc2148acb/docs/art/experiments/cryo_building_review_v1/evidence/godot/hr-a_rail.png)回看。
- 11 月 15 日接手时，家中有八项本机差异。同步得到的是 GitHub 已发布版本，立面审图也按已发布的候选比较。
  - 已改 `assets/art/cryo_building_review_v1/models/` 下的 `EXTERIOR_K01_common.glb`、`FA-A_complete_envelope.glb`、`FA-B_complete_envelope.glb`。
  - 已改 `docs/art/experiments/cryo_building_review_v1/model/facade_assembly_v1.blend` 与 `project.godot`。
  - 未跟踪 `ASSET_CREDITS.md`、`assets/art/room1_integrated_door_v3/room1_integrated_door_v3_door_front.png` 与 `assets/art/room1_open_hero_bake_r1/strip_irradiance.exr`。

给学校 Codex 的简短开场

> 同步 echoes-of-ruin 的 GitHub main，读 `docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md`。先打开 cryo_handrail_full_v1 审完整 C 双跑候选；正式场景尚未替换，不要从旧 A/B 或单段 C 继续扩展。
