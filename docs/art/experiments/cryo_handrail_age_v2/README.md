# C 一体化护栏｜按部位旧化 v2

2026-11-15。用户确认完整 C 的形体方向后，要求检查材质与旧化是否成立。本轮沿用完整双跑形体，补足长期静置的环境时间感。[同机位对比](preview.html) · [GitHub 对比](preview.md)

## 范围与材料身份

栏体解释为**隐藏结构支撑＋哑光矿物复合护面**，不解释为整块陶瓷承力。墙面继续是矿物基层／哑光面层；踏步与平台是灰色细骨料矿物耐磨面。造型、尺寸、位置、楼梯级数、灯条几何及实际游戏入口保持。各类非金属面的粗糙程度略有区分；旧化前后两列使用完全相同的材质参数与灯光。

旧化按照“建筑很少有人走动，环境变化为主”组织；80～90 年是故事时间，不作为计算积尘厚度、受潮程度或材料寿命的公式。没有新增漏水、锈蚀、持续客流或维修历史。

| 部位 | 本轮痕迹依据 | 保留完整的地方 |
|---|---|---|
| 栏体与墙侧握槽 | 槽底、受保护内缘及末端附近的细薄沉积，分段疏密变化 | 握持主面不画整条磨亮线，不把整个槽涂黑；端盖大面保留完整 |
| 墙脚与平台转角 | 实际接触线附近的成组旧膜／积层，向外细碎变淡 | 大面原本的像素颗粒仍是材料底纹，不全当灰尘 |
| 踏面靠墙端 | 沿墙侧接触位置分布，不同级取样连续变化 | 中间不画通行磨耗带、脚印、刮痕或漏液 |
| 灯槽及踏鼻 | 沿用既有构造和材质 | 不用发光、投影或整圈白边充当旧化 |

## PixelLab 与可编辑来源

三张主体旧化图通过 Chrome 扩展操作 PixelLab 官网 Creator 的 Edit Image / Pro Flash 生成；输入均为官网图库内已经存在的项目自有素材。未上传 Pixel Canals 内容，也未改换生成服务。

- `source/raw/mineral_edge.png`：护面／矿物墙脚接触沉积。
- `source/raw/groove.png`：握槽内的薄层沉积。
- `source/raw/floor_edge.png`：踏面靠墙端沉积。

全部为原生 256×256，未先缩小再放大。提示词和实际输入选择见 [生成记录](source/generation_record.json) 与 `source/prompts.json`。本轮消耗 **27** 次生成额度，账户从 9／2,000 到 36／2,000，余 **1,964**；网页显示下一重置／续费日为 **12 月 13 日**。

程序只负责真实部位遮罩、原生像素取样、配准、图集及导出，不生成污斑形状。不同位置改变取样相位，不把平移／翻转称为新增 AI 差分。Aseprite 母版分开保存原底材与 PixelLab 旧化层，合成结果与原始输出明确区分。

## 看什么、如何打开

Godot 4.6.2 打开 `scenes/dev/cryo_handrail_age_v2.tscn` 按 **F6**。1 看原材料，2 看按部位旧化，↑↓ 切机位，空格暂停人物与灯光演示。

A／B 均读取本轮同一套模型和图集坐标：A 使用底材图层，B 使用旧化合成。这样对比仅改变旧化像素，不把重新导入、曝光或光照差异混进结果。画面统一为 1280×720、最近邻；完整候选和代表近景一起交付，正式 Room 1、4F、F5 入口未替换。

技术巡检相机只用于本轮独立场景。墙面近景会临时隐藏遮挡的栏体，逐图记录隐藏对象；不把被挡住的墙脚算作已检查。像素密度、几何一致、来源核对与用户视觉审查分开记录。

本轮可编辑 Blender、便携 GLB、原生图集与 Aseprite 母版位于本目录及 `assets/art/cryo_handrail_age_v2/`。详细取样位置见 `source/placement_manifest.json`，模型与 UV 验证见 `model_manifest.json`，实际截图及相机状态见 `evidence/capture_record.json`。

- [Blender 工程](model/handrail_age_v2.blend) · [便携 GLB](../../../../assets/art/cryo_handrail_age_v2/cryo_handrail_age_v2.glb)
- [35 份分层 Aseprite 母版](../../../../assets/art/cryo_handrail_age_v2/editable/) · [35 套底材／旧化透明层／合成 PNG](../../../../assets/art/cryo_handrail_age_v2/textures/) · [母版回读](source/aseprite_readback.json)
- [六组接触部位前后对比](evidence/contact_comparison.jpg) · [32 张实际 Godot 截图及参数](evidence/capture_record.json) · [独立检查](evidence/independent_validation.json)

图集为按各面的实际长度组织的原生像素图集，不要求每张最终图都为 256×256；保持约 80 像素／米，图岛之间作两像素真实扩边。111 个网格的世界坐标、形体和拓扑与完整 C v1 一致，UV0 为部位配准重新排布。Aseprite 的底材、PixelLab 旧化和空白局部精修层独立保存；35 份母版导出与合成图的单通道误差不超过 1。Blender 的 40 张实际引用图片已内嵌，路径转为相对路径，见[跨电脑交付核对](evidence/blend_portability.json)。

父级已实际查看槽底、踏面接触、平台角、上下跑墙脚、背墙、端部及完整候选，并比较保底／有人照明。当前槽内灯条近景的分节亮暗在 A 底材中也存在，本轮没有重新设计灯光。审图没有使用 UV2 或烘焙，不把此次检查表述为正式房间光照验收。

复现顺序：Blender 运行 `model/build_age_v2.py`，再运行 `model/verify_age_v2.py`；Python 运行 `source/package_editable.py` 打包 Aseprite；Godot 导入后运行本轮场景并传入 `-- --capture`；最后运行 `build_review.py` 更新并排页与截图清单。

旧版 [完整 C v1](../cryo_handrail_full_v1/preview.html) 保留作来源和回退，本轮不覆盖它。实际移动控制器、碰撞爬楼、全楼安装和最终灯光仍按各自任务验证，不由材质对照代替。
