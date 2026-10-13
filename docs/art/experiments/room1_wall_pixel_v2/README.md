# Room 1 墙面像素贴图 v2 — 宽照明带与材质历史

2026-10-13。根据v1审图意见继续修改：灯带太细，墙面科技感与历史感不足。用户选约20～25cm宽照明带，并提出蓝色但不要太蓝。旧v1完整保留；本版等待审图。

## 本版改动

- 发光面从v1约5cm扩大到 **22.5cm**；仍靠墙顶、同高度、沿内墙连续经过门上方。
- 灯光试 **低饱和灰蓝白 `#CCDDE4`**，保留同镜头白光 `#EAEBDF` 对照。精准色值尚未确认，不锁定全项目灯色。
- 加强灯槽的金属翻边、密封阴面、下沿收边和少数围框接合点。接合点位于灯槽围框，未切断扩散罩／发光面。
- 下沿金属保护带的滚边、底部密封区、旧擦伤和钝化色差更清楚。
- 主墙面仍以 `#D3D6C9` 为主，`#E7E7D4`、`#C1C8BC` 提供色阶；加入更可读的面层失色、小缺损、边缘沉积。AI原生像素老化片段单独布置到各墙，减少重复损坏的规律。
- 主体结构保持完整；地板、休眠舱、门、房间布局与原审查灯光沿用。文字／编号仍留待下一轮。

方向参照 [当前墙面 Brief](../../ROOM1_WALL_TEXTURE_BRIEF.md)。本轮强化的是贴图中的结构与材料信息，未增加外露机械、通风口、屏幕、家具或密集板缝。

## 预览与源文件

- [对比预览](preview.html)：v1／v2、淡蓝／白光、正面近景与原生像素图。
- [Blender工程](room1_wall_pixel_v2.blend)：墙面颜色图及发光遮罩已打包，默认保存淡蓝试色；每个墙面材质的 `DIFFUSER_COLOR` 节点可独立改灯色。
- 淡蓝试色：[全室](evidence/01_wall_overview.png)、[低角度](evidence/02_wall_low_angle.png)、[正面近景](evidence/03_wall_detail.png)。
- 白光对照：[全室](evidence/04_white_light_comparison.png)、[正面近景](evidence/05_white_light_detail.png)。镜头、贴图、灯带尺寸及发光强度相同，仅换扩散罩的颜色／自发光色。
- 图像全部1920×1080；[后墙展开](evidence_wall_elevation.png)、[材料最近邻3倍](evidence_wall_material_nearest3x.png) 另供看原生像素。
- Aseprite母版：[后墙](editable/rear_wall_pixel_v2.aseprite)、[前墙](editable/front_wall_pixel_v2.aseprite)、[左墙](editable/left_wall_pixel_v2.aseprite)、[右墙](editable/right_wall_pixel_v2.aseprite)。

母版分层保留原生材料场、各墙独立AI老化片段、连续金属结构、真实墙角／旧接触痕迹、淡蓝扩散罩、隐藏发光遮罩、未经修改的AI参考与原创底图。

## 生成与整理的证据

使用 [官方PixelLab Pro编辑接口](https://api.pixellab.ai/v2/docs)，对 [原创400×272底图](guides/wall_layout.png) 进行1次细化，实际消耗 **15次订阅额度**。返回结果和余额差额一致，未充值。记录：[任务状态与用量](source/job_status.json)、[提示词](source/wall_edit_prompt.txt)、[原始结果](raw/wall_pro_00.png)。没有将Pixel Canals截图、贴图或模型作为AI输入。

AI生成了更明确的灯槽与面层历史，但也在输入段两端加了磨损边缘，整体底色偏亮。整理时将面层颜色校准到用户色板，剥离输入段边框，提取原生老化形状，以各墙专用透明图层单独布置。连续灯槽、保护带与精确发光遮罩由项目脚本绘制，保留材质／老化层来源，不将人工完成部分冒称为原始AI输出。

原创底图与实际提交的提示词使用更浅的青白 `#D5E4E5`，如实保留。试贴后该色在审查照明下过于接近白色，最终候选在整理层与可调材质节点中改为略偏蓝的 `#CCDDE4`，没有再次付费生成。

原生材料场使用镜像交替边缘衔接；明显旧痕迹单独安排，避免大损伤随材质段反复出现。前后墙1680×272、侧墙728×272，试值80 texels/m沿用v1，未宣布为全项目标准。

## 范围与限制

源工程为 `../room1_wall_pixel_v1/room1_wall_pixel_v1.blend`。所有原对象与原UV保留，仅六个内墙面追加v2平面UV、材质及图像。沿用v1正面材质相机，没有新增或重定位相机／模型。范围读回见 [structural_readback.json](structural_readback.json)。实际渲染及查看图像后再交付，艺术验收仍由用户审图决定。

灯带当前完成材质自发光及可调色，不含向室内投光的真实灯对象。原有审查照明保持，用于同镜头比较；画面不是最终应急环境亮度。低饱和蓝不等于让整室染成蓝色，Godot投光与人物／地面受光需后续单独验证。

约80～90年休眠、约70年以上城市无人期来自WORLD_BIBLE；墙面老化是依据材料与封闭设施条件作出的美术推演，清扫停止年份、材料配方和精确失效率仍不明确。不把未来灯带表现当作现实LED连续使用80～90年的工程证明。

## 复现与后续编辑

1. `source/prepare_wall_guide.py` 生成本版原创底图。
2. `source/pixellab_wall_job.py` 查询已记录任务。`submit`为付费生成，存在任务记录时拒绝重复提交；密钥沿用本机环境变量或已连接的官方Aseprite扩展，不进入仓库。
3. `source/finish_wall_maps.py` 从已保存raw整理图像与独立老化片段，无额外生成消费；需要Pillow、NumPy。
4. Aseprite批处理 `source/package_wall_masters.lua`，参数 `root=本目录`，保存分层母版和导出。
5. Blender后台 `apply_wall_materials.py` 另存v2并输出淡蓝／白光对照；可加 `-- --reuse-baseline` 复用已保存v1基准。

修改灯色只改 `DIFFUSER_COLOR`；保持同强度和同宽度即可复现白光／淡蓝比较。贴图母版已保存，再导出不必重新调用PixelLab。未做Godot迁移或运行测试。

## 参考归属

- [Pixel Canals技术研究](../../PIXEL_CANALS_REFERENCE.md)：借鉴几何与像素表面分工，未取用其资产。
- [ART_DIRECTION](../../../ART_DIRECTION.md) 第15–16节、[WORLD_BIBLE](../../../WORLD_BIBLE.md) 长期无人期与工业区供电说明。
- 舱体沿用项目自建低模；轮廓参考 [Scifi - Cryogenic Sleep](https://sketchfab.com/3d-models/scifi-cryogenic-sleep-3e65d80f30fb4a9e81f721f1c0cb8474)，作者 [Artboard Silvio Pinheiro / scrpinheiro](https://sketchfab.com/scrpinheiro)，GLB元数据许可 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。项目重建并修改头部窗、整片盖、有限开盖和脚端屏，未直接并入原参考网格。
