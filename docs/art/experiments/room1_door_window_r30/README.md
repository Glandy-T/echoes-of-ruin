# Room 1 认证小窗白边清理 r30

2026-11-03。只处理用户指出的认证小窗外围浅白圈，r29整体哑光门面及r28其余房间保持。新候选等待用户审图，正式F5未切换。

- [同机位与认证／通行对比](preview.html)；A为r29，B为r30，1280×720。
- F6：`scenes/dev/room1_door_window_r30.tscn`；1旧／2新。这里只切换门图，不切换舱材质。
- 导出：`assets/art/room1_door_window_r30/door_front.png`，112×184，不缩放。
- [Aseprite母版](editable/door_front_r30.aseprite)：继承r29原始分层，新增`r30_local_remove_white_bezel_keep_1px_dark_recess`独立精修层。
- [完整房间Blender](room1_door_window_r30.blend)：依赖本仓库相对路径资源，并非脱离仓库的独立单文件。

## 原因与处理

r29把旧v7的小窗22×14原生像素区域列入保护区，连同旧的浅白包边一并保留；周围PixelLab新门面比这圈旧颜色更暗，造成贴上去的白框感。不是认证灯额外产生的白色光晕。

本轮按已获准的Aseprite局部精修工作流处理该区域：外围接回邻近门面涂层颜色`#B7C0B3`，只留一像素暗色凹口边`#698281`，内部12×7原生像素保持精确不变。实际差异数量见`source/artifact_validation.json`。主体材质、做旧与来源仍是r29的PixelLab原图；本轮新增PixelLab请求0次、消耗0 generations，没有重抽主体，没有程序化污斑。局部像素清理通过Aseprite命名图层记录，`source/refine.lua`保留可复现操作。

## 验证与边界

`source/artifact_validation.json`核对差异严格限制在(45,61)–(66,74)，窗口内部和其余像素不变，Aseprite回读一致，81份既有依赖保持。`source/blender_readback.json`核对131对象、几何、UV、变换、相机和灯不变，只换一个门面图路径；相对依赖无缺失。

`source/runtime_validation.json`核对实际导入像素、单一贴图绑定、A/B/A恢复以及关闭／认证／授权状态。15张实际GPU画面保留游戏跟随镜头、全门与墙、斜侧、认证黄窗、开启绿灯及光晕；同机位A恢复精确一致。图像需实际打开检查，报告PASS不代替用户审查。

这次没有动GLB、UV0／UV2、烘焙图、原始／降噪光照、映射、门框灯、认证逻辑或其余全室材质。沿用r28既有整场景覆盖证据及本轮冻结校验，并补查受影响门区域；不声称此次重新做了整室光照／UV烘焙验收。既有r29保留回退。
