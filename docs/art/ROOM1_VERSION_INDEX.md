# Room 1：当前、正式与历史版本索引

**2026-11-04最新：4F整层外壳／走廊v3。** F6 `scenes/dev/cryo_4f_complete_v3.tscn`，48房间外壳，其他47间不放休眠舱，只做遮挡透明；Room1保留r30及20舱。八条走廊沿用r24墙／r26过道材质，整层配套烘焙完成，新增生成0次。E认证开门后，再对双面黑门洞按E进出，黑屏下180°换镜。F7透明、F8门外、F11总览、F12技术切区，权限锁定保留。预览及验证：`docs/art/experiments/cryo_4f_complete_v3/preview.html`（从仓库根解析）。其他房间室内和楼梯美术未制作，候选待审，正式F5仍r19。以下小样v1／v2为历史记录。

**最新走廊审查：配套烘焙v2。**F6 `scenes/dev/cryo_corridor_baked_v2.tscn`，F8到小样、F9灯带、F10 raw/降噪。复用r24墙／r26地坪，三个接收面共享UV2、4096采样、配套HDR，六个临时实时灯关闭。实际对照见 `docs/art/experiments/cryo_corridor_baked_v2/preview.html`（从仓库根目录解析）。下面“实时小样／尚未烘焙”为此前历史状态；正式F5仍r19。
**同日灯槽修复：**走廊墙板也已复用室内r24原生素材，取消重复独立灯管/横条，灯带遮罩与原图对齐，F9开关灯。开关/恢复同机位检查通过；走廊照明仍为实时小样，尚未做室内同等的配套烘焙。新增生成消耗0次。
**2026-11-04后续更新：**走廊小样已复用r26中央过道地坪（原生裁取，避开舱位与漏液）；门改为E互动后才认证，门洞双面黑色遮挡，开门后不可透视里外。本次新增PixelLab消耗0次。下方较早记录中的“地坪占位／自动认证”仅为历史状态。
2026-11-04新增独立[4F走廊小样v1](experiments/cryo_corridor_sample_v1/README.md)：继承r30，墙板候选、地坪占位；黑屏180°转向与邻室遮挡透明已实现并测试，正式F5未迁移。F6 `scenes/dev/cryo_corridor_sample_v1.tscn`，不替换下方室内素材基线。

核对日期：2026-11-03。此索引区分素材用途；用户已更新视觉与制作约束，见[像素美术制作基准](PIXEL_ART_PRODUCTION_STANDARD.md)。约束更新不代表下表素材已经返修或验收通过。

## 最新美术工作集

最新整室入口：`scenes/dev/room1_door_window_r30.tscn`（F6）。[门面与通行状态比较](experiments/room1_door_window_r30/preview.html)／[来源与验证](experiments/room1_door_window_r30/README.md)。用户已认可r28其余房间效果；r30在r29基础上只精修门面一个`pixel_map`，其余房间冻结，门形、开闭和灯语保持。

**已认可舱体／墙地基线r28**：[整室与逐舱比较](experiments/room1_pod_age_full_r28/preview.html)。4盖／4侧／3端合格面图组成20个唯一组合，编号01–20，非20套独立AI原图；r27 P12保持。用户表示其余效果可以，本轮只剩门面r30待审，不重开其他材质。

| 部分 | 实际来源 | 可编辑源／说明 |
|---|---|---|
| 四墙 | `assets/art/room1_wall_detail_full_r24/` | [r24](experiments/room1_wall_detail_full_r24/README.md)，四墙Aseprite在`editable/`。 |
| 连续无缝地坪 | `assets/art/room1_floor_detail_full_r26/` | [r26](experiments/room1_floor_detail_full_r26/README.md)，地板Aseprite在`editable/`。 |
| 20舱外壳 | `assets/art/room1_pod_age_full_r28/` | [r28](experiments/room1_pod_age_full_r28/README.md)：11张母材质、40张编号导出与固定安排JSON；原r22仍是A比较与继承依赖，不是最新外壳。 |
| 舱内、玻璃、屏幕、动画及共用部件 | v8几何、r16共用材质、r19运行整合 | [v8母版](experiments/room1_pod_standard_v8/README.md)／[r16来源](experiments/room1_pod_pixellab_r16/README.md)。 |
| 门面 | `assets/art/room1_door_window_r30/` | [r30](experiments/room1_door_window_r30/README.md)待审；只去认证窗白边；保留r29 PixelLab主体，r29作A基线，灯芯r17／柔光r18保持。 |
| 房壳、布局与全室光照 | `assets/art/room1_complete_r19/`等继承资源 | [r19](experiments/room1_complete_r19/README.md)。本轮未重烘。 |
| 最新整室Blender | `experiments/room1_door_window_r30/room1_door_window_r30.blend` | 使用同一仓库的相对路径图；不是独立于仓库的单文件交付。 |

细节完成度参照是已认可的墙r23、地坪r25 C和舱r27，完整实施基线为r28。主要面原生密度与做旧已推广，用户本轮认可其余效果；只有门r30待审，不再把r22旧缩放方案当长期例外。

## 正式游戏基线

F5标题进入`scenes/areas/military_facility/cryo_room_4f_01_3d.tscn`，继承r19；其墙地材质仍是r13／r15，舱体材质为r16体系，不等于上表最新美术候选。正式游戏入口没有在本轮切换。

## 历史与仍在使用的依赖

当前控制脚本继承链包含 **r30 → r29 → r28 → r27 → r26 → r25 → r24 → r22 → r19**，再继承更早实现。编号旧不代表文件无用。旧名称资源可能仍参与加载；保留运行依赖，不按编号删除父脚本。

以下只作历史参考，不作新制作标准：

- [r20颗粒／明暗试验](https://github.com/Glandy-T/echoes-of-ruin/tree/main/docs/art/experiments/room1_pixel_cluster_r20)：曾用于风格比较；不是全项目统一参数。
- [r21更粗颗粒试验](https://github.com/Glandy-T/echoes-of-ruin/tree/main/docs/art/experiments/room1_pixel_cluster_r21)：用户更偏好上一轮，不继续推广粗颗粒。
- r22旧墙面／旧地板分别由r24／r26后继；舱外壳由r28后继。r22仍是继承与比较基线，不再作为最新材质制作源。
- 早期纯2D、旧尺寸、旧门面和旧表面返工：只供追溯，不能覆盖GitHub当前设定及最新用户要求。

本机采用稀疏检出，仅隐藏不在当前源工作集中的历史实验目录；GitHub内容和提交历史不删除。需要回看时先用GitHub链接，或按[本机恢复说明](LOCAL_WORKSPACE_HANDOFF.md)恢复指定目录。不要为回看一个旧图切换整个项目到旧提交。

## 后续更新规则

每次完成新候选，只更新本索引对应部分，写清替代了哪一层、仍继承什么、正式入口是否切换。后续遵从2026-11-02制作基准，认可后冻结，不能从任一旧版文件属性推导新规格，也不继续无目标扩展试验。
