# 继续制作交接｜2026-11-15

11 月 15 日最新交付为 [C 一体化护栏按部位旧化 v2](experiments/cryo_handrail_age_v2/preview.md)。在完整双跑 C 上补了 PixelLab 环境旧化：槽底薄膜、实际墙脚和平台转角沉积、踏面靠墙端痕迹。大面保留完整，不画人为通行磨耗。形体、布局、灯条和约 **80 原生像素／米** 保持。正式场景尚未替换；[完整 C v1](experiments/cryo_handrail_full_v1/preview.md)与[原单段灰模](experiments/cryo_handrail_integrated_v1/preview.md)保留作来源和回退。

## 继续时先打开

1. 在学校副本检查 `git status --short --branch`，再同步 GitHub `main`。如果有同路径的本机差异，先保留并比较，审图以仓库提交为准。
2. 打开[最新 C 旧化对比](experiments/cryo_handrail_age_v2/preview.md)或[本地 HTML](experiments/cryo_handrail_age_v2/preview.html)，先看槽底、墙脚、踏面接触和平台角，再看完整双跑。A／B 为相同图集坐标、镜头、材料参数和照明下的底材／旧化合成。其他建筑候选继续从[原并排审图](experiments/cryo_building_review_v1/preview.md)查看。
3. 用 Godot 4.6.2 打开 `scenes/dev/cryo_handrail_age_v2.tscn` 按 **F6**。1 看底材、2 看旧化，↑↓ 切机位、空格暂停演示、L 演示灯光故障。旧灰模／像素表面对照仍在 `cryo_handrail_full_v1.tscn`；其他建筑候选入口为 `scenes/dev/cryo_building_review_v1.tscn`。

## 当前结果与下一步

| 项目 | 目前状态 | 接手后的判断 |
|---|---|---|
| ST-01 楼梯墙面与踏面 | 最新 v2 以实际逐级接触线配准墙脚旧膜，平台转角和踏面靠墙端有成组沉积；中央没有交通磨耗。大面沿用既有 PixelLab 细矿物底材。 | 先审 v2 的位置逻辑、强度及像素颗粒；不要把旧版与本轮沉积叠加使用。 |
| HR-C 一体化扶手 | 完整双跑 C 形体沿用 v1；最新 v2 补槽底及受保护内缘薄层，墙侧握槽有效深度仍约 65 mm。解释为隐藏结构支撑＋哑光矿物复合护面，不是整块陶瓷承力。 | 审查 v2 材质／旧化后再安装。两跑和转台约 1.80 m 净宽来自 v1 实测；安装时继续验证实际控制器与门扫掠。 |
| FD、EL、EN、FA | 各两款均已出 Godot 实拍。FD/EN 的独立样段验证了闭门阻挡与开后中心通行；EL 警示条可穿过，断电门叶仍挡住角色。FA 是 16F＋B4 外壳候选。 | 各组可独立挑选。FD 落地前复查整扇扫掠；EN 的首层外门位置待确认。FA 正式布光与远景运动采样仍待验证。 |
| 4F v6 与主角 | 4F 镜头、显现触发和强度仍待选。主角 3D 已暂停，身体 v2 保留，最后一版 Tripo 白袍未通过，游戏里继续用纸片占位。 | 先看建筑审图。恢复 4F 或主角时从下方的独立入口接手。 |

**扶手当前交付**。[最新 Blender](experiments/cryo_handrail_age_v2/model/handrail_age_v2.blend)、便携 GLB、35 份分层 Aseprite、35 套原生图集和 32 张 Godot 同机位截图见 [v2 说明](experiments/cryo_handrail_age_v2/README.md)。111 个网格形体与 v1 一致，UV0 为部位旧化重新排布并作两像素扩边。原始 PixelLab 图、实扣和母版回读均保留。净宽射线与静态胶囊通过不等于碰撞爬楼控制器已完成；本轮未使用 UV2／烘焙。

**美术约束**。楼内优先表现长期静置的环境变化，避免人为踩踏和喷漆式污斑。Pixel Canals 用作观察参考，绝不上传其内容。PixelLab 负责主体绘画，Aseprite 分层配准及局部精修。11 月 15 日 v2 三张新图消耗 **27**，账户累计 **36／2,000**，剩 **1,964**；网页显示下次重置／续费为 **12 月 13 日**。旧的 1994／2000 属上一期。[最新生成记录](experiments/cryo_handrail_age_v2/source/generation_record.json) · [M11 材料与岁月痕迹](cryo_building_production/MATERIALS_AND_AGEING.md)

## 复查、旧入口和本机差异

- 审图用独立实时光。已在 Godot 4.6.2 核对同机位画面与楼梯灯光演示，并比对导出模型的贴图密度、握轨坐标和立柱落脚高度。技术核对完成，视觉选择和正式安装仍待定。[审图说明及验证记录](experiments/cryo_building_review_v1/README.md)
- 正式 Room 1、F5 与旧 4F 路线继续沿用各自入口。要看 4F，用 `scenes/dev/cryo_4f_camera_compare_v6.tscn` 按 F6，再按 F8 去走廊。要恢复主角，先读身体和白袍的各自验收状态。[4F v6 审图](https://github.com/Glandy-T/echoes-of-ruin/blob/95899d39b7b0bf21138a7418668780af79e3ac7f/docs/art/experiments/cryo_4f_camera_compare_v6/preview.html) · [身体 v2](https://github.com/Glandy-T/echoes-of-ruin/blob/95899d39b7b0bf21138a7418668780af79e3ac7f/docs/art/experiments/protagonist_tripo_body_v2/preview.html) · [白袍检查](https://github.com/Glandy-T/echoes-of-ruin/blob/95899d39b7b0bf21138a7418668780af79e3ac7f/docs/art/experiments/protagonist_tripo_robe_h31_v1/preview.html)
- 学校机上次使用的 Godot 路径为 `E:/卒業制作/GODOT/Godot_v4.6.2-stable_win64_console.exe`。学校当前安装和项目路径到校后再核对。早期的 4F 操作表、主角诊断和学校工具路径仍可从[11 月 7 日交接归档](https://github.com/Glandy-T/echoes-of-ruin/blob/eea90b0cfa3c2fe82ec1778618f7feedc26ad30f/docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md)查到。上一版楼梯可从 [`f9a3746` 同机位](https://github.com/Glandy-T/echoes-of-ruin/blob/f9a3746c218853eec56d33c441afb6cdc2148acb/docs/art/experiments/cryo_building_review_v1/evidence/godot/hr-a_rail.png)回看。
- 11 月 15 日接手时，家中有八项本机差异。同步得到的是 GitHub 已发布版本，立面审图也按已发布的候选比较。
  - 已改 `assets/art/cryo_building_review_v1/models/` 下的 `EXTERIOR_K01_common.glb`、`FA-A_complete_envelope.glb`、`FA-B_complete_envelope.glb`。
  - 已改 `docs/art/experiments/cryo_building_review_v1/model/facade_assembly_v1.blend` 与 `project.godot`。
  - 未跟踪 `ASSET_CREDITS.md`、`assets/art/room1_integrated_door_v3/room1_integrated_door_v3_door_front.png` 与 `assets/art/room1_open_hero_bake_r1/strip_irradiance.exr`。

给学校 Codex 的简短开场

> 同步 echoes-of-ruin 的 GitHub main，读 `docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md`。先打开 cryo_handrail_age_v2 审完整 C 的按部位旧化；形体沿用 full_v1，正式场景尚未替换，不要把旧痕与新版叠加，也不要从旧 A/B 或单段 C 继续扩展。
