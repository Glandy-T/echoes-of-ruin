# Room 1 连续哑光地坪 A/B 候选

2026-10-13。**待审，尚未选定 A 或 B。** 用户要求“两个都试试看，对比一下”。

## 查看与选择

[并排比较](preview.html) 提供总览、低角度与平面核对三组截图，每张均为 1920×1080。

| 候选 | 色彩组织 | 可编辑源文件 |
|---|---|---|
| A | 全室统一蓝灰基调 | [Blender](floor_A_uniform_v1.blend) / [Aseprite](editable/floor_A_uniform_v1.aseprite) |
| B | 同一表面，既有通道略亮、舱区略暗 | [Blender](floor_B_tonal_zones_v1.blend) / [Aseprite](editable/floor_B_tonal_zones_v1.aseprite) |

两版使用同一哑光微纹理、墙边收口和淡接触细节。分区没有独立道路模型、地面高度差或砖缝。B 的色差在边缘以五级色阶过渡；当前约 0.30 m 过渡宽度仅为试验。

比较重点：统一表面是否更适合正式、封闭的休眠设施；微弱色差是否有助于读出通行区域，同时仍像整片地坪。

## 配色与制作方法

用户参考色为 `#5A6C73`、`#7D9298`、`#415763`、`#253943`。A 以主色为中心；B 当前通道名义底色 `#64777D`、舱区 `#54676F`，均为本轮候选，不是项目调色板标准。

1. 自绘 400×400 连续哑光材质导图与文字说明，以官方 PixelLab REST 接口请求一次 Pro 编辑。没有提交 Pixel Canals 原作截图、贴图或模型。
2. 保留 [原始结果](raw/floor_pro_00.png) 和 [提示词](source/floor_edit_prompt.txt)。AI 虽被要求不要划痕，仍加入了泛用划痕；最终并非直接使用该结果。通过局部中值替换与色阶约束压制高对比划痕，保留低对比材质起伏。
3. 将整理后的共用材质镜像重复映射到现有整片地面，再依据工程中的墙边、门洞与既有通道坐标绘制确定位置的收口及 B 分区。
4. 只在两处现有舱体邻近位置保留极淡的接触痕迹示意。它们不是确认过的历史损伤，也未进行材料老化模拟。没有随机散布脏污斑块。
5. 保存分层母版：共用材质、B 分区、共用收口、局部接触、隐藏的 AI 原始参考。B 母版隐藏 `02_B_color_zoning_hide_for_uniform` 图层即可回到统一色方案。

PixelLab 本次任务实际用量为 **25 次订阅额度**，见 [job_status.json](source/job_status.json)。A/B 共用这一份生成结果，没有为 B 再发生成请求。接口调用脚本不保存令牌；需要现有官方服务凭据，具体读取方法沿用仓库既有直连助手。

## 场景范围与来源

两版均从暂时保留的 [墙面 v2 工程](../room1_wall_pixel_v2/room1_wall_pixel_v2.blend) 独立建立。

- 地面顶面追加一份平面 UV 和最近邻过滤的哑光材质；原 UV、地面侧面与底面保留。
- 房间尺度、十字布局、20 个舱体、门、墙面、原灯光、原相机位置保持一致。使用现有三台相机分别对照，无新相机或设备。
- **墙面 v2 尚未获得视觉认可**，用户暂时保留；它的斑块、灯带和照明问题不因本次地板比较而通过审查。
- 全室舱体仍为原工程灰模；之前单舱贴图候选未在本次传播到全室。
- FreeCAD / 工程布局仅提供尺寸、位置和空间关系，没有移植 CAD 几何造型。

坐标来源：[engineering_layout.json](../room1_full_lowpoly_v1/source/engineering_layout.json)。制作范围依据 [地板 Brief](../../ROOM1_FLOOR_TEXTURE_BRIEF.md)、现行 [ART_DIRECTION](../../../ART_DIRECTION.md)、[WORLD_BIBLE](../../../WORLD_BIBLE.md) 与 [Pixel Canals 研究](../../PIXEL_CANALS_REFERENCE.md)。历史信息用于限制表现方向，无法推导确切清洁停止日期或磨损形状。

## 文件与复现

- `textures/floor_A_albedo.png`、`floor_B_albedo.png`：1680×760 地面颜色图。
- `textures/common_matte_material.png`：400×400 共用材质。
- `textures/manifest.json`：试验色组、通道坐标和接触位置。
- `source/prepare_floor_guide.py` → `source/pixellab_floor_job.py` → `source/finish_floor_maps.py` → `source/package_floor_masters.lua`：导图、生成记录、整理和分层母版流程。已提交过生成任务的脚本禁止自动重复提交。
- `apply_floor_variants.py`：在 Blender 5.0.1 后台建立两份工程并输出六张截图；两份工程已打包图像。
- `structural_readback.json`：生成时记录对象结构、变换、原 UV 和非地面对象范围检查。该记录不证明最终美术验收或 Godot 运行效果。

## 尚待验证

材质具体化学组成、老化细节、最终像素密度与 Godot 显示规格均 TBD。目前按 21×9.5 m 外围地面映射，80 texels/m 只是本轮贴图密度。Blender 沿用原灯光及显示变换，因此截图颜色会与原始色值不同。

本轮像素细节较安静，重点比较分区。Pixel Canals 所体现的轮廓、结构、材质与像素信息层级继续作为方向；仅添加噪点无法达成该效果。后续需要在整室贴图和最终受控镜头下再判断像素颗粒与细节密度。
