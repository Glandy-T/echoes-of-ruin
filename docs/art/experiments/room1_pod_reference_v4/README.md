# Room 1 休眠舱 v4 — 按参考重建

2026-10-13 · **单舱美术与动作候选，待用户审图。**

## 本轮要求与处理

用户要求以提供的休眠舱参考为主进行复刻与简化，减少自由设计；玻璃窗和开闭采用本项目方案，小部件留给后续像素贴图。

本次重新构建低模网格。生成脚本不读取原 GLB，不沿用 v1–v3 网格，也不使用 FreeCAD 占位几何。参考 GLB 仅在另一个临时 Blender 会话中用于观察和测量。

| 部位 | v4 处理 |
| --- | --- |
| 总体 | 恢复参考的低矮比例；约长 2.30 m × 宽 1.05 m × 高 0.67 m，仍在原 1 m 高工程占位内 |
| 前端 | 保留长斜挡板与横向端面，用少量折面近似参考的圆角过渡 |
| 后端 | 保留较短的端帽，与前端区分 |
| 上部 | 直线长边框、宽顶面、斜肩；上盖贴近端部最高沿 |
| 下部 | 低侧壁、下沿支撑裙板、小幅底部净空、前部下横撑 |
| 玻璃 | 删除躯干段大玻璃，只保留头部窗口；当前蓝灰色为区域预览，尚非最终玻璃 Shader |
| 舱盖 | 一整片刚性罩壳；端部外壳固定，整个中部盖罩先抬起，再向一侧滑转 |
| 小构件 | 不单独建螺栓、侧面孔列、通风格栅、小扣件、按钮、窄槽；后续按需画贴图。前端小罐体省略 |

`comparison.html` 左侧为实际参考灰模观察图，右侧为本次重建，采用接近的低角度与同种 Workbench 显示，方便看主形。参考原作的全身玻璃与本作头部玻璃差异是本次有意修改。

## 参考比例依据

原 GLB 主壳外包约 `0.24096 × 0.54021 × 0.15398`，高/宽约 `0.639`。按宽 1.05 m 适配时高度约 0.67 m；按长 2.30 m 单独等比换算高度约 0.656 m，两者略有差别，因此本轮在既有平面占位内采用约 0.67 m 高。它取代的是先前美术候选的厚重比例，**没有改写 Room 1 工程布局或工程文件**。

原透明罩自身约占主壳长的 68.5%、宽的 89.2%；罩顶约为主壳最高沿的 98.1%。这些测量说明盖应嵌在边框里。它们不是 v4 整片可动盖的尺寸：v4 的整片盖同时包含不透明躯干板、头窗周围框架和侧肩，运动边界经过修改。

## UV 与后续像素贴图

已做实际接缝展开，不是自动坐标投影占位：

- 固定舱体、整片盖、内部睡眠面各有一份独立 0–1 UV。
- `uv/` 中包含透明 PNG 线稿、SVG 区域图和实际面 UV 坐标 JSON。
- `07_uv_checker.png` 是保存前实际渲染的棋盘格观察图；棋盘格图像已打包到 Blender 工程。
- `1024×1024` 仅为展开图导出尺寸，不是最终像素贴图规格。

当前 UV 随待审形状提供，尚未锁定全项目像素密度、三张贴图的分辨率比例、UV 岛朝向、图集合并和最终接缝修饰。没有运行自动 UV 重叠/拉伸测试，也没有完成像素绘制或 Godot 材质验收。后续应在形状确认后整理这些参数，再开始正式绘图。

## 开闭示意与边界

Blender 时间线：1 帧关闭；30 帧抬起约 0.13 m；60 帧侧移中间状态；90–108 帧在侧边打开。`whole_lid_motion.gif` 来自实际 Blender 动画渲染。盖子是同一个刚性对象，头窗随盖一起运动。

本轮保留“抬起 → 侧移并顺截面转下”的方向，**最终收纳位置仍是候选**。低矮舱体与整片宽盖之间存在尺寸关系：本次侧边竖置的盖上缘仍高于舱体，没有声称已全部藏进侧壳。导轨、是否需要更低的倾斜终点、占用哪侧操作空间以及邻舱之间的净空，需下一步单独确认。没有修改 Room 1 通道或相邻舱来迁就此动作。

本次完成真实渲染、参考对照与棋盘格目视查看；没有运行运动碰撞、人物上下舱或整排舱体的测试。旧版本的检查结果不继承到本版。

## 文件与复现

- [Blender 源文件](room1_pod_reference_v4.blend)
- [参考与本轮对比](comparison.html)
- [关闭状态](evidence/01_closed.png)
- [打开状态](evidence/04_open.png)
- [完整开闭示意 GIF](evidence/whole_lid_motion.gif)
- [UV 棋盘格](evidence/07_uv_checker.png)
- `build_pod.py` / `model_tools.py`：重建几何、UV、可编辑动作并渲染静帧。
- `render_motion.py`：渲染动画预览帧。
- `package_guides.py`：使用 Pillow 编码 GIF、导出 UV PNG。
- `motion_poses.json`：可追溯的动作参数。

在本目录使用 Blender 5.0.1 运行：

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' --background --factory-startup --python-exit-code 1 --python .\build_pod.py
& 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' --background --factory-startup --python-exit-code 1 --python .\render_motion.py
python .\package_guides.py
```

保留 v1、v2、v3；未扩展完整房间，未修改建筑小样、人物、CAD、Godot 或下载的 GLB。

## 来源与署名

设计参考与对照图来源：**[Scifi - Cryogenic Sleep](https://sketchfab.com/3d-models/scifi-cryogenic-sleep-3e65d80f30fb4a9e81f721f1c0cb8474)**，作者 **[Artboard Silvio Pinheiro / scrpinheiro](https://sketchfab.com/scrpinheiro)**。

用户提供 GLB 的 `asset.extras` 标记许可为 **[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**。`evidence/09_reference_observation.png` 是原模型的灰模观察渲染。v4 按其设计重建新的低模拓扑，修改了窗分区、开盖方案，简化了小部件；不是原作者的未修改模型或认可作品。后续使用此候选及参考图时保留本节署名、来源、许可与修改说明。原始 GLB 未上传到本目录。
