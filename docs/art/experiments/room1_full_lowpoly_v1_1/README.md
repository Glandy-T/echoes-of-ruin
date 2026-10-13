# Room 1 全室低模 v1.1 — 取消门旁认证面板

2026-10-13。根据用户本轮提出的方案，Room 1 主门改按门前自动识别个人芯片的方向推进，移除独立的壁面认证面板。主门造型仍为占位，旧 v1 完整保留。

## 当前方案

- 人靠近门前，系统读取个人芯片并判断通行权限；通过后自动开门。
- 认证功能整合到门的系统内，本轮不添加可见感应器、按钮或额外壁面设备。
- 既有文档 `ART_DIRECTION.md` 第18.3节已规定主人公具备参与者基本通行权限；`CRYO_FACILITY_LAYOUT.md` 也包含自动读取个人芯片的流程。
- 这次只调整 Room 1 的交互方向与美术占位，不将所有区域的门统一改为自动门。后续失去能源区域的门状态仍按各场景设定处理。

具体感应范围、触发条件、无权限反馈、关门时机及失电状态为 **TBD**。当前 Blender 工程不实现检测、权限判断或门动画。

## 这版改动

- 从全室 v1 移除 `AUTH_PANEL_PLACEHOLDER_NOT_APPROVED` 对象及其无使用者的数据。
- 门集合更名为 `03_AUTO_CHIP_DOOR_PLACEHOLDER_TBD`，并记录门的交互方向。
- 原有房间尺寸、20个休眠舱、门洞、占位门、UV、镜头和审查灯光均沿用 v1。
- 用相同三个镜头重新输出 1920 × 1080 图像。

空间输入和建筑 UV 参照 [v1 来源与 UV](../room1_full_lowpoly_v1/README.md)。v1 中认证面板的 UV 仅属于旧版，不再用于本版。所有仍使用的几何、材质、UV 均已包含在新 `.blend` 文件中，可单独打开。

## 文件

- [三张预览](preview.html)
- [Blender 工程](room1_full_lowpoly_v1_1.blend)
- [修改脚本](revise_room.py)：读取相邻 v1 工程，另存 v1.1；加 `-- --render` 输出三张图。
- [全室](evidence/01_full_room.png) / [低角度](evidence/02_low_angle.png) / [俯视](evidence/03_top_plan.png)

图像用于查看去掉面板后的建筑立面；不代表正式门造型、最终贴图、游戏运行结果或人体工学验证。

## 休眠舱参考归属

休眠舱仍为 v4.1 自建低模候选。轮廓参考 [Scifi - Cryogenic Sleep](https://sketchfab.com/3d-models/scifi-cryogenic-sleep-3e65d80f30fb4a9e81f721f1c0cb8474)，作者 [Artboard Silvio Pinheiro / scrpinheiro](https://sketchfab.com/scrpinheiro)，用户提供 GLB 的许可元数据为 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。以新网格重建，并改为头部窗口、整片舱盖、有限开盖和脚端信息屏。原参考网格未直接并入本工程；保留来源、许可与修改说明。
