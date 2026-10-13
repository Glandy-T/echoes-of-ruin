# Room 1 连续纯色墙／地面小样 v1

2026-10-13。按用户本轮要求“墙壁地板先做成一体纯色”，在全室 v1.1 上另存材质小样，旧版本完整保留。

## 本轮成果

- 墙体：统一浅象牙灰，RGB **211 / 212 / 198**。
- 地面：统一蓝灰，RGB **90 / 108 / 115**。
- 这两个临时试色来自已认可休眠舱 v2 的颜色，不代表最终项目色板。
- 每种材质的贴图只有一种颜色；没有分块网格、接缝、划线、污渍、斑点或新增细节。房间墙面虽保留门洞所需的多个 mesh，表面视觉连续。
- 图中的渐变和阴影来自原有灯光，不是贴图上的图案。仍沿用原有审查材质流程，没有声明为最终像素 Shader。
- 纯色图使用脚本直接生成，**不是 PixelLab 输出**。PixelLab 接口的真实验证、原始生成结果与实际扣费另见 [接入记录](../pixellab_direct_api_check_v1/README.md)。

## 预览与源文件

- [对比预览](preview.html)：旧版／本轮相同镜头，以及三张本轮图。
- [Blender 工程](room1_wall_floor_solid_v1.blend)：两张贴图已打包，可单独打开。
- [全室](evidence/01_solid_overview.png)、[低角度](evidence/02_solid_low_angle.png)、[俯视](evidence/03_solid_top_plan.png)：全部 1920×1080，沿用原镜头。
- [墙面 Aseprite](editable/wall_solid_v1.aseprite)、[地面 Aseprite](editable/floor_solid_v1.aseprite)：可编辑单色基础图层。
- [墙面 PNG](textures/wall_solid.png)、[地面 PNG](textures/floor_solid.png)、[颜色记录](colors.json)。32×32 只为当前文件尺寸，恒定颜色不定义像素密度。
- [试贴脚本](apply_solid_surfaces.py)、[纯色图脚本](source/prepare_solid_maps.py)、[母版脚本](source/make_editable.lua)。

复现：先用 Python 运行 `source/prepare_solid_maps.py`，再用 Blender 后台执行 `apply_solid_surfaces.py`。需保留相邻 `room1_full_lowpoly_v1_1/` 作为源工程。Aseprite 批处理打开对应 PNG，通过 `--script-param output=目标文件` 执行母版脚本。

## 范围与检查

源工程：`../room1_full_lowpoly_v1_1/room1_full_lowpoly_v1_1.blend`。模型、墙地轮廓、门、20个休眠舱、位置、原有 UV、灯光和镜头沿用源版。休眠舱仍使用全室源版的灰模材质，未在此次墙地任务中推广或修改已认可的单舱 v2。

[结构读回](structural_readback.json) 记录 136 个对象，材质更换前后对象变换、顶点、面拓扑和 UV 相同。实际渲染并查看全室／低角度图，墙地表面连续，没有加上原始 API 小图的花纹。Aseprite 母版已通过批处理保存；Blender 图像已输出。

本轮只供确认连续表面与基础颜色，未做 Godot 导入或运行测试，也不意味着纯色墙地替代了已认可的 Pixel Canals 总体美术质量目标。接下来需要用户审图后再决定表面信息与最终材质表现。

## 休眠舱来源

沿用全室 v1.1 中自建低模，轮廓参考 [Scifi - Cryogenic Sleep](https://sketchfab.com/3d-models/scifi-cryogenic-sleep-3e65d80f30fb4a9e81f721f1c0cb8474)，作者 [Artboard Silvio Pinheiro / scrpinheiro](https://sketchfab.com/scrpinheiro)，用户 GLB 中许可为 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。重建网格、头部窗口、整片舱盖、有限开盖和脚端信息屏为项目修改；原参考网格没有直接并入本工程。
