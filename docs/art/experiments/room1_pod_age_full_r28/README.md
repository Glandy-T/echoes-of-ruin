# Room 1 全20舱做旧与原生像素差分 r28

2026-11-02。用户已认可全20舱及其余房间效果，要求最后修正门面；后续见[r29门面](../room1_door_material_r29/README.md)。本目录保留完整舱体与墙地基线，正式F5仍为r19。

## 查看与继续制作

- [整室新旧与逐舱对比](preview.html)。A＝已认可r27 P12＋其余旧r22外壳；B＝r28全20舱安排。不是把P12退回旧版再作比较。
- F6：`scenes/dev/room1_pod_age_full_r28.tscn`；默认B全室，1旧基线／2全室、O只开闭P12、H说明。没有更换正式F5入口。
- 完整房间Blender：`room1_pod_age_full_r28.blend`，外部图为同一仓库相对路径，不是单独一个blend就包含全部依赖。
- 11份Aseprite母版：`editable/`，按A/B/C/D及lid／shell_side／shell_end命名；D没有单独端面，因为拒用了不合格输出。
- 运行资产：`assets/art/room1_pod_age_full_r28/`，包括11张面图、40张编号导出及固定安排`layout_variants.json`。

## 差分与编号

**4种盖板、4种侧壳、3种端面，共11个独立合格面图来源，错开组成20个不重复的整舱组合。**不是20套独立AI原图，也不把翻转／旋转／变色算新绘画。A三个面图逐字节复用已认可r27；B/C各三张、D盖板／侧壳两张为本轮新PixelLab输出。

每类盖板和侧壳的A–D各用于5舱，端面A/B/C分别7／7／6舱。同排相邻和前后对应舱避免使用同一侧壳或端面，盖板也错开。全部物理位置保持，不靠重新排布遮掩重复。P12采用A/A/A，与已认可r27三面图逐像素一致。

编号01–20沿用既有3×5数字字形与原编号板位置。只在功能编号板内转移数字，不重复UNIT文字、不改变屏幕的人名／状态布局。40张盖板／端面编号图配有`source/number_layers/`的透明编号层，可重复导出；编号之外与所选原生材质逐像素一致。

## 原生像素与制作方式

盖板96×184、长侧184×56、端面96×56，沿用r27按真实UV测量的原生尺寸，主面约78–84纹素／米。斜肩／窄条的既有UV差异仍保留，本轮没有重展UV，不宣称每个小倒角都严格80。

主体仍由PixelLab官方`POST /v2/inpaint-v3`制作，输入只含本项目已认可材质／原创结构及遮罩；未上传Pixel Canals的NoAI图片、模型或贴图。保留提示词、原始输入／输出、任务ID和用量。所有被采用的创作输出没有缩放、模糊或程序化污斑；遮罩是精确结构／编号保护，白区由新AI材质替换，不与旧做旧层混合。

共**10次成功请求、100 generations**，其中8张新图被采用。D端面第一次原样返回A输入，补做一次又过于干净，均拒用；两份raw、请求／结果和原因保留在`source/rejected_outputs.json`，不冒充独立差分。最终选用三种合格端面完成20组合，不为凑第四种继续抽卡。

Aseprite分层保留原创结构、原生PixelLab材质、功能编号及局部精修层；本轮没有强行增加手绘，局部美术精修层为空。功能数字是精确技术导出，不称为新AI材质。

## 保持与验证边界

只更换20舱×3个外壳`color_map`绑定。模型、UV、房间尺寸和布局、墙地、门、灯光／GI、玻璃、床面、双侧灯管、动态屏幕及功能权限不变。其他19舱仍关闭且不能开盖；只对P12检查实际开闭，不用缺少开盖GI的其他舱制造假演示。没有新烘焙，材质颜色导致的间接反弹变化尚未重算。

- `source/artifact_validation.json`：95项检查通过，含原生尺寸、11份Aseprite回读、差分真正不同、40份编号只改编号板、P12精确保持和实际用量。
- `source/baseline_hashes.json`：21份既有工程、模型、墙地、光照及已认可r27源未变。
- `source/blender_readback.json`：131对象几何／UV／位置／灯／相机保持；只换60处外壳图，外部依赖无缺失和绝对路径。
- `source/runtime_validation.json`：216项运行检查通过；60绑定对应44个唯一运行PNG，实际Texture2D尺寸／解码像素与源一致。
- `source/capture_validation.json`及`evidence/capture_record.json`：43张最终1280×720 GPU帧，A→B有差异、A→恢复逐像素一致；覆盖六游戏机位、20舱近景、四角、P12开闭与basecolor总览。两张检查sheet只是派生图，不混计为GPU帧。
- `source/independent_review.json`：独立核验51个PNG的源／导入MD5、11母版、编号、Blender范围及实际截图，通过；用户最终美术认可另列。

正式游戏迁移与最终配套烘焙不在本轮进行。技术检查通过不代替用户整室视觉认可；认可后冻结，不继续无目标返修Room 1，随后准备主角低模和像素贴图。

## 无需再次生成的复现

使用已保存raw运行`source/layout.py`、`compose.py`，以Aseprite批处理执行`package.lua`（参数`root`为实验绝对路径），再运行`check_artifacts.py`。完整Blender源由`blender_material_source.py`从r27另存。不要为重新打包再次运行付费POST；`jobs.py`使用已有任务状态防重复提交。

Godot先完整执行`--headless --editor --path . --import --quit`，再运行verify；GPU捕获使用**非headless**的`--rendering-driver opengl3`完整capture路径。稀疏检出需保留本实验目录；所有缓存／日志／个人配置与旧blend备份不上传。
