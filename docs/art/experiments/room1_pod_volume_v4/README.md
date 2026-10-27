# 休眠舱 v4：实体截面、透明头窗与像素旧化

2026-10-27，单舱候选，等待美术审查。旧 v3 和整室均保留，没有替换20个舱。

## 本轮范围

沿用已认可的参考轮廓、整片侧滑盖、仅头部留窗和脚端大屏。闭合外包络约1.05 × 2.294 × 0.665 m；Blender第1帧闭合、第60帧沿用45°开盖终态。没有重新设计开盖路径，也没有扩展全室。

实测原模型不是完全没有厚度：盖中央薄板约11.7 mm，曲面玻璃约8.6–11.7 mm，床垫40 mm。问题包括薄截面缺乏可读性、屏面没有背壳、两个竖直内壁使用XY投影导致UV面积为零。新版本增加内衬厚板、舱口密封肩、窗框及显示器浅凹背壳；修复这两个内壁的截面UV。新增结构随原父级运动，不在已有双面玻璃上重复Solidify。

## 贴图与玻璃

八份分层Aseprite在[editable](editable/)，运行PNG在[textures](textures/)。保留v3设计底层和隐藏原图，新旧化独立分层，截面另有可编辑母版。颜色仍为低饱和冷灰蓝结构和浅色外壳；不依靠整屏降分辨率制造像素感。

Pixel Canals的方法在此落实为：几何承担轮廓与必要实体截面，像素图承担装配暗槽、涂层块面、沿接合和接触位置的积旧。大面保留完整区域，不随机撒斑点。这里只借鉴方法，不复制其建筑或纹理。

长侧面不重复UNIT01；顶盖及端面暂用单舱样本编号12，头端UV单独纠正方向。屏幕保留NAME/SYS占位行和两条状态条，没有编造人物名字或具体生命数据，最终动态UI另做。

头窗保留真实曲面厚度，改用显式alpha的局部像素反光，透明基底与反光分别控制。新玻璃没有自发光；舱内可见度由实际内腔光和真实内部几何产生。玻璃关闭／隐藏、舱内灯亮／灭及反光关闭均有控制截图，不用一块发光蓝色面假装透明。

## 审图与Godot导入

- [同机位对比页](preview.html)
- [打包Blender源](room1_pod_volume_v4.blend)
- 独立场景：`scenes/dev/room1_pod_volume_review_v4.tscn`，在Godot中F6运行。
- V：v3/v4；O：闭合/45°打开；1–6：审图机位；G：舱内光；T：玻璃显隐；R：像素反光；H：说明。
- 导出位于 `assets/art/room1_pod_volume_v4/`，闭合与打开分别为静态GLB。每个材质分块保留实际使用UV为TEXCOORD_0。

所有对比为实际Godot GL Compatibility输出1280×720，同组旧新共用相机和灯光。**这是独立单舱审图布光，不是整室新烘焙、最终游戏照明或新的Room 1镜头方案。** 裸GLB带嵌入基础材质；玻璃最终表现依赖附带Godot Shader与审图脚本，不能把普通GLB预览当成同一渲染。

模型与像素贴图候选未自动推广到整室。下一步先审打开后的厚度、头窗透明度、屏幕结构及旧化强度，再做20舱状态/编号差分、正式材质绑定和配套烘焙。当前不包含新的碰撞、人物动画或完整运行时开盖动画。地面r9仍是用户暂时搁置的候选，不因本轮通过而视为批准。

## 可复现与验证

1. Python运行 `source/build_textures.py`；Aseprite批处理运行 `source/package_textures.lua`。本机工具路径只用于执行，不是资产依赖。
2. Blender后台运行 `source/build_volume_pod.py`，重新打包源文件并导出两种姿态；运行 `source/validate_volume_geometry.py`读回保存后的工程。
3. Godot导入后用 `--rendering-method gl_compatibility --resolution 1280x720 --script res://docs/art/experiments/room1_pod_volume_v4/capture.gd` 实际渲染。
4. 运行 `source/check_delivery.py`核对八份母版重开导出、GLB嵌入图和玻璃控制往返；结果在 `source/quality_check.json`。几何读回在同目录JSON。

本轮无新PixelLab或其他AI生成调用，没有新增生成额度消耗。旧v3 PixelLab来源、原图与母版留在原实验目录。本轮为项目资产上的可编辑像素返修。

## 参考来源

外观主参考为用户下载的“Scifi - Cryogenic Sleep”（Artboard / Silvio Pinheiro，scrpinheiro），沿用原 `room1_pod_reference_v4_1` 的来源记录；该记录载明CC BY 4.0。本轮未重新核验第三方在线授权，不把旧记录当成新的授权调查。当前项目低模几何由已有重建源继续返修，未重新导入第三方高模。

风格方法参考：[Pixel Canals](https://sketchfab.com/3d-models/pixel-canals-low-poly-game-level-0e7cd01efb484aff817e3b03425cc080)，既有研究见 `docs/art/PIXEL_CANALS_REFERENCE.md`。不宣称获知其原始UV、Shader或精确贴图分辨率。
