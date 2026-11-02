# Room 1：当前、正式与历史版本索引

核对日期：2026-11-02。此索引区分素材用途；用户已更新视觉与制作约束，见[像素美术制作基准](PIXEL_ART_PRODUCTION_STANDARD.md)。约束更新不代表下表素材已经返修或验收通过。

## 最新美术工作集

整室入口：`scenes/dev/room1_floor_detail_full_r26.tscn`（F6）。

**P12单舱待审候选r27**：[开闭同机位对比](experiments/room1_pod_age_r27/preview.html)／[来源与验证](experiments/room1_pod_age_r27/README.md)，F6 `scenes/dev/room1_pod_age_r27.tscn`。仅P12三张外壳图统一原生颗粒并补足做旧；未推广其他舱。完整Blender候选与三份Aseprite位于该实验目录；全室其余部分仍以下表r26来源为准。

| 部分 | 实际来源 | 可编辑源／说明 |
|---|---|---|
| 四墙 | `assets/art/room1_wall_detail_full_r24/` | [r24](experiments/room1_wall_detail_full_r24/README.md)，四墙Aseprite在`editable/`。 |
| 连续无缝地坪 | `assets/art/room1_floor_detail_full_r26/` | [r26](experiments/room1_floor_detail_full_r26/README.md)，地板Aseprite在`editable/`。 |
| 20舱外壳 | `assets/art/room1_pixel_unify_r22/` | [r22](experiments/room1_pixel_unify_r22/README.md)：编号盖板／端面与A–D侧壳。不能误写成仍全用r16。 |
| 舱内、玻璃、屏幕、动画及共用部件 | v8几何、r16共用材质、r19运行整合 | [v8母版](experiments/room1_pod_standard_v8/README.md)／[r16来源](experiments/room1_pod_pixellab_r16/README.md)。 |
| 门面 | `assets/art/room1_integrated_door_pixellab_v7/` | [v7](experiments/room1_integrated_door_pixellab_v7/README.md)；门框灯芯r17、柔光r18。 |
| 房壳、布局与全室光照 | `assets/art/room1_complete_r19/`等继承资源 | [r19](experiments/room1_complete_r19/README.md)。本轮未重烘。 |
| 最新整室Blender | `experiments/room1_floor_detail_full_r26/room1_floor_detail_full_r26.blend` | 使用同一仓库的相对路径图；不是独立于仓库的单文件交付。 |

细节完成度参照是用户已认可的[墙面r23](experiments/room1_wall_detail_r23/README.md)与[地板r25 C](experiments/room1_floor_detail_r25/README.md)。差分分布可变，但不能退回近乎空白。整室候选与局部基准的审查状态分别记录。**r22舱外壳不作为长期密度例外；r27已完成代表舱候选，等待审图，其他19舱尚未推广。**

## 正式游戏基线

F5标题进入`scenes/areas/military_facility/cryo_room_4f_01_3d.tscn`，继承r19；其墙地材质仍是r13／r15，舱体材质为r16体系，不等于上表最新美术候选。正式游戏入口没有在本轮切换。

## 历史与仍在使用的依赖

当前控制脚本继承链包含 **r26 → r25 → r24 → r22 → r19**，再继承更早的门、角色、光照与房壳实现。编号旧不代表文件无用。`assets/art/`、`scripts/dev/`和`scenes/dev/`的旧名称资源可能仍参与加载；本次保留运行依赖，未通过删除父脚本来整理目录。

以下只作历史参考，不作新制作标准：

- [r20颗粒／明暗试验](https://github.com/Glandy-T/echoes-of-ruin/tree/main/docs/art/experiments/room1_pixel_cluster_r20)：曾用于风格比较；不是全项目统一参数。
- [r21更粗颗粒试验](https://github.com/Glandy-T/echoes-of-ruin/tree/main/docs/art/experiments/room1_pixel_cluster_r21)：用户更偏好上一轮，不继续推广粗颗粒。
- r22旧墙面／旧地板：分别由r24／r26后继；**r22舱外壳仍在使用**。
- 早期纯2D、旧尺寸、旧门面和旧表面返工：只供追溯，不能覆盖GitHub当前设定及最新用户要求。

本机采用稀疏检出，仅隐藏不在当前源工作集中的历史实验目录；GitHub内容和提交历史不删除。需要回看时先用GitHub链接，或按[本机恢复说明](LOCAL_WORKSPACE_HANDOFF.md)恢复指定目录。不要为回看一个旧图切换整个项目到旧提交。

## 后续更新规则

每次完成新候选，只更新本索引对应部分，写清替代了哪一层、仍继承什么、正式入口是否切换。后续遵从2026-11-02制作基准，认可后冻结，不能从任一旧版文件属性推导新规格，也不继续无目标扩展试验。
