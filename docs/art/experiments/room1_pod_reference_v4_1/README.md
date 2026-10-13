# Room 1 休眠舱 v4.1 — 开盖终点与信息屏

2026-10-13。用户认为 v4 大体可用，本轮仅作两项局部修改；v4 原文件保留。

## 修改

1. **缩短开盖动作**：用户图一对应 v4 动画约第 60 帧。将该 **45°** 姿态作为完全打开终点；60 帧后保持，不再继续翻至 90°。之前的抬起、侧移路径沿用 v4。
2. **脚端信息屏**：在用户图二所指脚端上方斜面加入一个浅嵌入屏幕。根据用户“屏幕有点小”的后续反馈，可视面扩大到 **0.470 × 0.195 m**，比初版面积约增加 48%；边框收窄，凹入约 4 mm。周边仅增加很少的面，屏幕自身为一张四边形面。没有添加按钮、指示灯或独立设备。

选择少量几何的理由：屏幕边界及浅凹陷在斜角下仍能读出。屏幕文字、状态条、图标、表面细节与发光表现留给后续像素贴图及 Godot 材质。当前深色空白只表示屏幕位置，不是最终 UI 或“断电”设定。

## 源文件与 UV

- [Blender 工程](room1_pod_reference_v4_1.blend)
- [预览页面](preview.html)
- [完全打开姿态](evidence/02_open_45deg.png)
- [屏幕近景](evidence/03_display_close.png)
- [动作 GIF](evidence/opening_45deg.gif)
- [UV 棋盘格](evidence/04_uv_checker.png)

屏幕是独立对象 `Foot_info_display_surface`，有独立材质和 0–1 UV，方便以后替换静态像素图或动态显示内容。屏幕模板导出为 512×212，仅用于当前比例下的绘图导引，不锁定项目贴图规格。

舱体原有 UV 没有重新打包。仅在被替换的斜面内插原 UV，增加浅槽与边沿；盖、床面保持原 UV。所有模板见 `uv/`。棋盘格材质和图像设置了保留标记，随工程保存。

## 复现与范围

`revise_pod.py` 从相邻的 `../room1_pod_reference_v4/room1_pod_reference_v4.blend` 读取已保留的基线，局部修改后另存 v4.1；不修改基线。它使用 v4 的 `model_tools.py` 与 `motion_poses.json`。打开本版 `.blend` 本身不依赖脚本执行。

使用 Blender 5.0.1 运行 `revise_pod.py` 生成工程及静帧，再运行 `render_motion.py` 生成帧；用 Python + Pillow 运行 `package_guides.py` 打包 GIF 与 UV PNG。

本次实际渲染并查看了关闭、45° 打开、屏幕近景及棋盘格。没有运行自动测试、碰撞验证或 Godot 运行验证。屏幕内容、交互逻辑、导轨细节仍待后续制作。房间尺寸、舱位、建筑、人物和 Godot 工程未修改。

## 来源

延续 [v4 的来源与修改说明](../room1_pod_reference_v4/README.md)：造型参考 [Scifi - Cryogenic Sleep](https://sketchfab.com/3d-models/scifi-cryogenic-sleep-3e65d80f30fb4a9e81f721f1c0cb8474)，作者 [Artboard Silvio Pinheiro / scrpinheiro](https://sketchfab.com/scrpinheiro)，用户提供 GLB 标记许可为 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。v4 使用新低模网格重建并修改窗与开盖；本版继续增加浅信息屏并缩短动作。使用时保留来源、许可及修改说明。
