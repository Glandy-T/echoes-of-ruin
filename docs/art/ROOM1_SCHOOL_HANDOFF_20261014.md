# Room 1 — 学校电脑交接（2026-10-14）

这份交接对应2026-10-13夜间至14日凌晨的墙地、单舱文字与 Godot 导入适配。**最新 GitHub main 是交接来源**，不要使用学校旧缓存覆盖它。

## 到学校先做

1. 学校仓库没有未提交工作时执行 `git pull --ff-only origin main`；若有学校本地改动，先检查／另存，再合并，禁止直接 reset 覆盖。
2. 阅读本文件和 [本轮审图页面](experiments/room1_material_revision_v1/preview.html)。先看墙地时间感的强度；新图仍待用户审查。
3. 用 **Godot 4.6.x** 打开仓库根 `project.godot`。本机验证版本4.6.2；无需在学校配置 Blender 导入路径，因为游戏用文件是嵌入贴图的GLB。
4. 等待导入完成，到 `assets/art/room1_revision_20261013/` 打开GLB的高级导入预览。可将它们拖入新的 `Node3D` 审图场景，另存到 `scenes/dev/`；不要直接覆盖现有2D主场景。
5. 快速看布局用 `room1_layout_review_r1.glb`。正式组织完整室内时用 `room1_shell_full_r1.glb`，需要剖切可读性时只在审图副本隐藏前墙、左墙、屋顶。主门仍占位。
6. 单舱用 `pod_closed_v3.glb`，开盖终态比较用 `pod_open_v3.glb`。若放回20个既有位置，参考 `pod_placement_godot.json`；**不要把贴图舱叠在 layout-review 的灰模舱上**。

## 今天已确认／已完成

| 内容 | 状态 |
|---|---|
| 地板A统一方向 | 用户选定；不做十字通道色差 |
| 地板r1 | 连续蓝灰，低对比大面材料变化、边缘轻微压暗、极淡接触；新图待审 |
| 墙面r1 | 暖灰配色保留；删除随机脏斑老化贴片；按角、脚、门洞、保护带组织时间感；新图待审 |
| 灯带 | 22.5cm淡灰蓝白、原高度与发光遮罩保持；最终投光未做 |
| 休眠舱v3 | 两长侧重复UNIT01已删除；显示屏为姓名、系统字段、两条状态条 |
| 姓名与运行数据 | 空／静态占位，不是最终设定或真实状态 |
| Godot适配 | 四份GLB均已实际导入并实例化，贴图材质最近邻；未验收游戏画面 |

## 最新文件

- 墙地 Blender：`docs/art/experiments/room1_material_revision_v1/room1_material_revision_v1.blend`
- 墙地分层母版：同目录 `editable/`，5份 `.aseprite`；原生PNG在 `textures/`。
- 单舱 Blender：`docs/art/experiments/room1_pixellab_pod_trial_v3/room1_pixellab_pod_trial_v3.blend`
- 单舱分层母版：同目录 `editable/`，7份 `.aseprite`；原生PNG在 `textures/`。
- 游戏导入包：`assets/art/room1_revision_20261013/`，4份GLB及实际Godot导入配置。
- 源导出记录：墙地r1、单舱v3各自 `godot_export/manifest.json`，脚本 `export_godot.py`。
- 实际导入读回：[godot_import_readback.json](experiments/room1_material_revision_v1/godot_import_readback.json)。

旧版完整保留。本轮新增 PixelLab 用量 **0**。本地密钥、应用配置、临时日志和 `.godot` 缓存不随交接上传。

## 导入适配细节

- 坐标换算：Blender `(x,y,z)` → Godot `(x,z,-y)`。房壳单位米、尺度1；房间外围21×9.5m，内净20.6×9.1m，沿用当前工程。门在后墙中央；没有改变舱位置。
- 导出副本把各面真正使用的UV整理到 `TEXCOORD_0`。原 `.blend` 的UV仍保留，不能从“只导出第一层UV”简化回退，否则贴图会错位。
- 墙面使用直接颜色图和RGB发光图；单舱导出普通贴图材质。Blender专用三档色阶节点不等于可直接导入Godot的Shader。
- `.glb.import` 设置 `gltf/embedded_image_handling=3`（无损嵌入）、关闭自动LOD与动画导入，并绑定 `nearest_pixel_import.gd`。四份模型实际读回的纹理过滤均为 `0 / NEAREST`。
- `docs/.gdignore` 已添加，文档中的 Blender、原始贴图和试验工程不再被Godot当运行素材重复导入。引擎使用 `assets/art/` 的交付包。
- 本机导入在隔离最小项目进行；保存的是可复用设置，学校首次打开仍会生成自己的 `.godot` 缓存。首次受本机配置目录权限影响，完成正常权限导入后，最终四份资源均成功读入。

依据：[Godot 4.6导入配置](https://docs.godotengine.org/en/4.6/tutorials/assets_pipeline/importing_3d_scenes/import_configuration.html)、[GLTFState嵌入图像模式](https://docs.godotengine.org/en/4.6/classes/class_gltfstate.html)、[BaseMaterial3D最近邻](https://docs.godotengine.org/en/4.6/classes/class_basematerial3d.html)。

## 明天的推进次序

1. 先确认墙地r1和单舱v3设计，不因已经导出而视为验收。
2. 在Godot审图场景里确认米制、UV、最近邻、实际镜头下像素颗粒和遮挡。完整房壳会包含前／左墙和屋顶，这是正常的完整模型。
3. 给新的3D审图场景安排Godot灯光，确认淡蓝灯带与墙地受光；当前灯带自发光不能证明会照亮房间。
4. 再决定三档／受控明暗 Shader 的Godot实现。普通PBR导入与Blender受控色阶版的观感会不同，应保留比较。
5. 如要推进可走动原型，再单独建立碰撞、导航／受限移动、舱交互、连续开盖动画、门禁和动态屏幕。静态开盖GLB不具备这些功能。

这轮没有修改原游戏主场景、Viewport、移动方式或新增游戏玩法。下一位Codex继续时，先沿用最新用户确认和GitHub现行美术方向；FreeCAD仍只作尺寸、位置、空间关系参考。

## 学校续作：Godot 实际搭建（2026-10-14）

- 用户审查认为墙地 r1 太干净、看不出时间痕迹，暂不通过；学校电脑今天先做导入搭建，材质返修延后。
- 已新增 `scenes/dev/room1_import_review_r1.tscn`：完整房壳、20个 v3 贴图舱、三个检查镜头和基础灯光。打开该场景按 F6；1/2/3 切换镜头，F 切换完整房壳，L 切换审图灯光，O 切换 P12 静态开盖终态。
- 项目关闭 `.blend` 自动导入，避免本地旧工作素材要求配置 Blender；运行素材仍使用 GLB，原母版保留。
- 四份GLB已在本工程实际导入、实例化，最近邻与UV0读回、20舱位置／朝向、剖切与静态姿态切换均检查通过；保存了5张真实Godot截图。未新增玩法或改原主场景／Viewport。
- 近景显示贴图与屏幕；各舱仍复制01，前排端面编号存在倒向／镜像表现，后续逐面UV和标识检查。灯光只是试排，Godot受控色阶Shader未实现。
- 操作与验证见 [Godot搭建说明](experiments/room1_godot_review_r1/README.md) 和 [读回](experiments/room1_godot_review_r1/validation.json)。
