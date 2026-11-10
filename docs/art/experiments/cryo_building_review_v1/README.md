# 标准休眠楼｜建筑候选审图 v1

[本地并排审图](preview.html) · [GitHub 并排审图](preview.md) · [逐图相机、状态和交付清单](review_manifest.json)

以 GitHub main 的 `f7fa9e8342f77106daad9b9199f34333fca53c89`、[建筑美术执行包](../../CRYO_BUILDING_ART_PRODUCTION_PACK.md) 和冻结标准层 `v3_trim` 为基线。交付五组 A/B 十款造型，以及 ST-01 双跑样段和 K-01 共用配件。所有候选均为独立审图，等待用户选定。Room 1、正式 F5、4F v6、正式交互和主角工作没有替换。

| 组成 | 入口 |
|---|---|
| 模型 | [室内 Blender 工程](model/interior_accessories.blend)、[整栋立面 Blender 工程](model/facade_assembly_v1.blend)、[独立 GLB](../../../../assets/art/cryo_building_review_v1/models/) |
| 贴图 | [原生 PNG](../../../../assets/art/cryo_building_review_v1/textures/)、[15 份分层 Aseprite](editable/)、[原始 PixelLab 图](raw/)、[来源与局部精修记录](source/material_packaging.json) |
| 实际画面 | [Godot 截图](evidence/godot/)、[28 秒动态照明](evidence/stair_motion_28s.gif)、[原生像素裁片](evidence/materials/) |
| 尺寸与校验 | [室内尺寸](model/interior_manifest.json)、[样段验证说明](model/interior_QA.md)、[立面旧化位置](facade_material_placement.json)、[GLB UV0 密度](evidence/uv0_density.json)、[碰撞实测](evidence/godot/runtime_probes.json) |

用 Godot 4.6.2 打开 `scenes/dev/cryo_building_review_v1.tscn`，按 F6。数字 1–0 对应 HR-A/B、FD-A/B、EL-A/B、EN-A/B、FA-A/B；↑↓ 切镜头，O 控制两扇门，C 切换电梯警示，L 切换楼梯保底照明。项目中的旧 2D 精灵只作尺度参照。每组 A/B 共用机位、曝光和画幅。立面另有四向、节点、首层、屋顶和地下技术机位。

## 贴图与尺度

Pixel Canals 用来校准像素颗粒、连贯块面与细节完成度。15 张新主体材质由 PixelLab Creator 的 Pixen / Pro Flash 制作，六张沿用项目现有材质或原生裁片。上传的是项目原创导图；有些导图使用已有 M03 项目材质作底。单独添加 r24 风格参照的请求未完成。Pixel Canals 及其他第三方作品只用于观察。

原图、[实际提示词](source/creator_submissions.json)、[下载校验](source/official_downloads.json) 和[实扣](source/usage_summary.json)可分别追溯。23 张原图共扣 95 单位（14×1、9×9），余额从 101 降到 6，未购额外额度。`generation_plan.json` 是提交前估算。编辑遮罩在 Aseprite 打包阶段用于保护边界，不冒称服务端按遮罩作图。母版分开保存导图、PixelLab 原图、受保护像素和局部精修；独立导出与最终 PNG 做了逐像素比对。

主要表面以 **80 原生贴图像素／米** 为准。FD/EN 正面 144×192 对应 1.8×2.4 m；EL 正面 112×192 对应 1.4×2.4 m；256×256 外墙面对应 3.2×3.2 m。报告由实际 GLB 的 UV0、几何边和 PNG 原生尺寸测得；曲面、极窄收口和斜面局部有差异。近景使用最近邻；远景材质预留了 mipmap 采样设置，但本轮 PNG 导入未生成 mipmap，远景运动时的闪烁仍待正式场景验证。1280×720 是审图画幅，屏幕上的像素大小仍受距离、投影和倾角影响。

## 技术结论与待决项

- HR 两款成品可以比较握轨和护栏；约 1.62 m 的实测净宽小于工程 1.80 m，选款不等于可安装。
- FD、EN 的独立样段实测闭合阻挡与开扇后中心通行。冻结的楼梯平台上还须检查整扇扫掠和有效宽度。
- EL 以闭合停运交付。警示可穿过、实际门挡住角色；调用件无运行发光，无认证或电梯运行逻辑。
- EN 没有确认的首层出口锚点，两款均为 ASSET ONLY。冻结 CAD 中 D089–D096 是内核 2.4 m 旁通口，没有冻结门高与封闭门定义，保留开口；K-01 不新增机器门或锚点。
- FA 两套以相同结构轮廓与 16F＋B4 比较横向和竖向板格。外露基座压深、屋顶压顶、两处有源雨痕均有固定位置。地下只作为技术视图，室外天气、走廊最终布光和正式烘焙仍未验收。

## 复现

使用 Blender 5.0.1 后台运行 `model/build_interior_accessories.py` 和 `model/build_facades_v1.py`，生成 GLB 与带项目贴图的 Blender 源文件。通过 Godot 编辑器导入，然后运行审图场景并传入 `-- --capture`，得到完整截图记录。用 Python + Pillow 运行 `source/audit_uv0.py`、`source/build_evidence.py`、`source/build_review_index.py`，生成审图页、UV 检查、接触表与 28 秒 GIF。GIF 来自实际渲染的 112 帧；连续帧不重复提交，生成命令可复现。该样段只用实时光，不复用正式 UV2 或烘焙。
