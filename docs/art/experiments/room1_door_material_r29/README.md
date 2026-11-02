# Room 1 门面哑光材质与做旧 r29

2026-11-02。用户已认可r28其余房间效果，要求最后修正门的“不锈钢感”和做旧。本轮是**门面单张颜色图候选，等待审图**；墙、地、20舱和已认可照明冻结，正式F5未切换。

## 查看与文件

- [新旧同机位与认证／开启检查](preview.html)。A为r28使用的v7门面，B为r29；全部1280×720。
- F6：`scenes/dev/room1_door_material_r29.tscn`；默认B，1旧／2新。既有自动认证、横向滑门和框内绿灯／柔光保持。
- 运行PNG：`assets/art/room1_door_material_r29/door_front.png`。
- 分层母版：`editable/door_front_r29.aseprite`。
- 完整房间源：`room1_door_material_r29.blend`，由r28另存，仅替换门面图；依赖同仓库的相对贴图路径。

## 观察与改动

原Godot门面Shader为`unshaded`，`SPECULAR=0`；没有需要降低的实际金属高光。旧v7颜色图保留斜向大面明暗带，且主面较平滑，容易读成金属板。这里将不锈钢感主要归因于绘入贴图的明暗与材质信息不足，是结合贴图／Shader观察作出的判断，而非改动真实反射参数。

新图采用与设施相符的哑光矿物／陶瓷复合涂层：去掉旧的斜向亮带，不画反射、拉丝或方向性光照；表面增加细碎的涂层色差、边缘成组接触沉积、密封收口与状态窗附近的材料时间感。保留完整主面，不添加锈黄、大片剥落、新设备、门缝或额外框层。

本轮**只换`panel_material.pixel_map`一个绑定**，不改Shader、光照衰减曲线、UV、门形、门框、状态窗、开闭／权限逻辑、碰撞、框内绿灯及光晕。保持实际受光方式，避免同时改变曝光掩盖贴图效果。没有重烘GI，也未改走廊灰盒设计。

## PixelLab与Aseprite来源

使用官方`POST /v2/inpaint-v3`，一次成功请求，实际**10 generations**。实际任务ID、提示词、输入／遮罩及原始输出均保留；没有追加抽卡或改换生成工具。

输入是本项目自有256×192画布：左侧在(4,4)放置112×184原创平色门导图，保护原门轮廓／小状态窗；右侧为已认可r24墙面的原生裁片作材料与颗粒语境，受黑遮罩保护。墙图也是项目自有资产，没有上传Pixel Canals的NoAI内容。原门白区的旧明暗和旧做旧不叠入新材质。

最终门面只原生裁切`raw/door.png`的(4,4)–(116,188)，精确遮罩配准，**没有缩放、模糊或脚本污斑**。112×184覆盖既有1.4×2.25m门面，约80～82纹素／米。完整原图包含右侧参考语境，不作为门面整张拉伸使用。

Aseprite母版保留原创平色结构、新PixelLab材质和局部精修层。本轮局部精修层为空，仅进行了结构配准／分层，不虚称为手绘精修。

## 检查与边界

- `source/artifact_validation.json`：原生尺寸、RAW白区像素、保护结构、Aseprite回读、实际任务及Blender范围检查。
- `source/baseline_hashes.json`：79份既有工程／模型／Shader／灯／墙地／全部r28材质及已认可源保持。
- `source/blender_readback.json`：131对象的几何、UV、变换、材质槽、灯与相机不变，仅一个门面图路径更新；外部图无缺失／绝对路径。
- `source/runtime_validation.json`：运行时实际Texture2D尺寸与解码像素、源／导入MD5、A/B/A单一绑定以及门状态、其余房间材质不变。
- `source/capture_validation.json`和`evidence/capture_record.json`：最终GPU截图的实际相机、状态、材质及恢复比较。真实游戏取景与技术近景分别记录，不能把手动近景当成游戏相机。

验收仍看实际房间里的待机关闭、黄窗认证和绿灯通行状态，不以“调低金属度”或文件检查代替视觉判断。用户未认可前保留r28／v7作回退，不重开其余房间风格。

复现已有素材无需新请求：先用保存raw运行`source/compose.py`，以Aseprite批处理运行`package.lua`（参数`root`），再执行`check_artifacts.py`；Blender由`blender_material_source.py`从r28另存。Godot先完整导入，再运行verify；GPU capture必须使用非headless的`opengl3`。
