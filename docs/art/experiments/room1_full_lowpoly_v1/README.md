# Room 1 全室低模 v1 — 空间骨架与休眠舱母版布置

2026-10-13。用户已同意先建立完整 Room 1，并明确主门外观尚未决定：本版在后墙中央保留实际门洞与简洁占位门，供审查房间尺度、舱位、动线和镜头，不将占位门视为正式设计。

本目录从 GitHub main 快照 `16405cf08a06bebd84b45509d988ec83e7a68a66` 中的工程文件读取 Room 1 尺寸与坐标；工程文件仅作为尺寸、位置和通路依据。墙、地面与门的低模外壳在 Blender 中重新搭建，没有导入或复刻 FreeCAD 几何。

## 本版内容

- 房间内净尺寸为 **20.6 × 9.1 m**；可见净高 **3.4 m（暂定）**。
- 后墙正中门洞为 **1.4 × 2.4 m（暂定）**，门洞位置、纵向入口轴线及横向主通道沿用工程布局。
- 20 个已关闭的 Room 1 休眠舱 v4.1，逐一放在 [`source/engineering_layout.json`](source/engineering_layout.json) 记录的坐标。它们保持现有长轴、朝向和空间关系，不在本版另行设计开盖姿态。
- 后墙的门旁认证面板仅保留极简占位体块。
- 墙与地面是连续、平整的低模大面，不加入网格、密集墙缝、铺砖缝、管线或额外设备。墙厚、门洞和必要的空间遮挡由几何承担；之后的编号、材料暗线、维护信息与表面细节将由像素贴图处理。
- 前墙、左墙和屋顶放在可隐藏的 `02_CUTAWAY_front_left_roof_hidden_for_review` 集合，便于从审查镜头看到室内；完整四面墙与顶板均已建好。俯视图显示四面墙，只剖去屋顶与门洞上方墙面，让门洞可读。

## 门的范围

`MAIN_DOOR_PLACEHOLDER_NOT_APPROVED` 只是一个适配门洞的简洁平面占位，不含最终门扇结构、开门机构、导轨、材质、编号或 UI。工程说明只要求人员门位于后墙中央，并记录向上开启的自动门逻辑；实际外观仍为 TBD。

后续确定门的造型后，应替换该对象，但保持门洞净宽、门洞位置和中央入口通道不变。认证面板同样仅确定位置与体块；屏幕内容、交互与显示状态尚未设计。

## UV 与贴图准备

休眠舱复用 v4.1 的 UV。建筑外壳为每个对象生成独立的平面 UV 岛，导出在 [`uv_architecture/`](uv_architecture/)：

- `Floor_continuous_no_tile_seams`：连续地面顶面与边缘；
- `Wall_*`：前、后、左、右墙及门洞上方墙面；
- `MAIN_DOOR_PLACEHOLDER_NOT_APPROVED` 与 `AUTH_PANEL_PLACEHOLDER_NOT_APPROVED`：仅作为未来替换贴图的边界参考；
- `Roof_hidden_for_cutaway`：完整壳体所需的屋顶面。

每个对象同时提供 SVG 和 JSON。它们说明当前 UV 边界，不锁定最终图集、贴图分辨率或 texel density；这些参数需要在固定/受控镜头及 Godot 原型中与像素资产一起验证。当前灰色材质仅用于检查轮廓、遮挡和比例，不能视为最终配色、灯光或贴图结果。

## 审查图与文件

- [Blender 工程](room1_full_lowpoly_v1.blend)
- [生成脚本](build_room.py)
- [工程布局输入](source/engineering_layout.json)
- [完整室内视图](evidence/01_full_room.png)
- [低角度构图](evidence/02_low_angle.png)
- [顶视平面核对](evidence/03_top_plan.png)
- [预览页面](preview.html)
- [建筑 UV](uv_architecture/)

截图中的灰色材质和渲染灯只服务于 Blender 审图。它们没有改动 Godot、FreeCAD 或现有场景文件。

三张图均为 1920 × 1080。01 为全室概览，02 为较低的候选镜头，03 仅用于查看布局。本次已生成并目视检查三张渲染图；没有进行游戏运行、开盖避让或人体工学测试。

重新生成：在 Blender 5.0.1 的后台模式运行 `build_room.py`；加上 `-- --render` 同时生成三张审查图。脚本依赖相邻目录中的 `room1_pod_reference_v4_1.blend`，保存后的全室 `.blend` 已包含舱体网格、材质和 UV，可独立打开。脚本会更新本 v1 目录，继续修改美术时应另存新版本。

## 尚待验证／决定

- 主门的正式轮廓、面板与开闭机构；
- 像素贴图、项目色板、最终材质和建筑图集规格；
- 最终 Camera 取景、投影和像素显示参数；
- 休眠舱舱盖打开后的扫掠范围、相邻舱净空与人员上下舱/转身舒适度；
- 人物的最终位置与模型；
- 3.4 m 室内净高，以及消防、机电等建筑技术要求。

本版不新增家具、独立终端、医疗推车、储物、管线、装饰设备或额外门。审图通过前，不将它扩展为贴图成品或 Godot 迁移。

## 休眠舱参考来源

本版沿用 v4.1 的休眠舱候选与来源说明：整体轮廓参考 [Scifi - Cryogenic Sleep](https://sketchfab.com/3d-models/scifi-cryogenic-sleep-3e65d80f30fb4a9e81f721f1c0cb8474)，作者 [Artboard Silvio Pinheiro / scrpinheiro](https://sketchfab.com/scrpinheiro)，用户提供的参考 GLB 标记许可为 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。本项目以新低模网格重建并修改为头部窗口、整片舱盖、有限开盖与脚端信息屏；没有把参考模型直接并入本工程。后续分发或使用时保留来源、许可及修改说明。
