# Room 1 材料时间感修订 r1

2026-10-13 夜间制作、2026-10-14 交接。**方向已确认，新图待审。** 旧墙 v2、地板 A/B、单舱 v2 均保留。

## 本轮内容

- 用户选 **A 统一蓝灰连续地坪**，不强调十字通道。增加低对比、数米尺度的连续材料色差，墙边轻微压暗，只有两处极淡的安装／接触示意。没有路线、砖缝、随机污渍或明显刮痕。
- 墙面保留原暖灰色组，**不再使用墙 v2 的 AI 老化贴片图层**。改为轻微大面色差；低强度沉积只在墙角、墙脚、门洞边；旧接触变化只落在下沿金属保护带。连续灯槽、金属翻边、收边和少数接合点沿用。
- 灯带仍为 22.5 cm、淡灰蓝白 `#CCDDE4`，遮罩和原材质自发光强度不变。
- [单舱 v3](../room1_pixellab_pod_trial_v3/preview.html) 删除两长侧的重复 `UNIT 01`；屏幕换为姓名栏、系统字段与两条静态状态条。姓名和真实运行数据没有填入。

[本轮审图](preview.html) 提供改前／改后同镜头和单舱近景。[Blender 工程](room1_material_revision_v1.blend) 是全室墙地修订；其中20舱继续保留原灰模，单舱贴图单独交付，没有把待审单舱自动铺到全室。

## 可编辑与来源

`editable/` 含地面及四个墙面的五份分层 Aseprite 母版：底色、大面材料变化、结构、位置明确的边缘沉积／接触层、灯带及隐藏发光遮罩。`textures/` 含颜色图、原发光遮罩及导出用RGB发光图。

这轮是**人工修改现有图层与生成脚本**，新增 PixelLab 调用／额度为 **0**。仅保留旧 PixelLab 材质极弱的微色阶；大面、结构与边缘由确定坐标的原创图层组织，没有随机生成器，也未加载被否决的老化贴片。

`source/build_material_layers.py` → `source/package_masters.lua` → `apply_material_revision.py` 可复现当前墙地。源图与密度沿用旧候选：地面1680×760，长墙1680×272，侧墙728×272；80 texels/m 仍是试验值。

工程尺寸与位置只参考既有工程布局，不复制 FreeCAD 几何。主体模型、门位置、20舱位置、UV、原相机与审查灯光不变，见 [结构读回](structural_readback.json)。接触痕迹是候选表现，不是确认过的历史事件，也没有模拟未来复合材料的老化年限。

## Godot 导入适配

[学校交接](../../ROOM1_SCHOOL_HANDOFF_20261014.md) 列出操作次序。运行资产位于仓库根目录 `assets/art/room1_revision_20261013/`。

- 完整房壳与剖切布局各一份 GLB；单舱关闭／45°打开各一份 GLB。
- 米制，Godot坐标为 Blender `(x,y,z)` → `(x,z,-y)`。
- 导出副本将每个面实际使用的 UV 写入 `TEXCOORD_0`；原 Blender UV 不删改。
- 墙面节点转换为 glTF 支持的 Principled＋颜色图／RGB发光图。单舱的 Blender 三档审图 Shader 转为普通贴图材质；没有将它冒称为 Godot 最终 Shader。
- GLB 嵌入PNG，随包提供 `.glb.import`：无损嵌入、禁用自动LOD、静态导入；`nearest_pixel_import.gd` 只对这四个文件设最近邻，不改全项目设置。
- **已在 Godot 4.6.2 隔离项目中实际导入并实例化四份资源**，读回的纹理材质过滤值均为 `0 / NEAREST`，见 [Godot读回](godot_import_readback.json)。这不等于游戏运行、碰撞、连续开盖动画或最终画面验收。

本轮未改变正式游戏主场景、Viewport、Camera 或移动方式。`docs/.gdignore` 让文档中的 Blender 母版与实验文件不参与正式 Godot 资源导入，避免重复转换；游戏用文件从 `assets/art/` 进入。

## 仍待确认

新版墙地强度待审；主门仍占位；角色姓名／屏幕语言／运行字段／真实条形数据 TBD；单舱顶盖与脚端原编号保持。完整关盖动画、门禁实现、碰撞／导航、最终照明和像素 Shader 在学校单独推进。没有新增模型装饰或设备。

参考方向见 [ART_DIRECTION](../../../ART_DIRECTION.md)、[墙面 Brief](../../ROOM1_WALL_TEXTURE_BRIEF.md)、[地板 Brief](../../ROOM1_FLOOR_TEXTURE_BRIEF.md) 与 [Pixel Canals 研究](../../PIXEL_CANALS_REFERENCE.md)。
