# Room 1 当前墙地配套烘焙 r7

2026-10-27。承接r6接缝修正和r5全室旧地坪／四处漏液，把当前颜色图接入Blender母版并完成配套irradiance烘焙。解决前几轮“换颜色图但仍借用旧固有色反射”的交付限制；没有新增美术设计或通过提亮改变气氛。

[实际对照页](preview.html) · [最新打包Blender工程](room1_surface_lighting_r7_packed.blend) · [校验记录](quality_check.json) · [源文件重开检查](source_readback.json)

## 本轮改变与保留

- 七个既有墙地颜色面：四面墙使用`assets/art/room1_seam_contact_r6/wall_*.png`，地面使用`assets/art/room1_surface_full_r5/floor_with_leaks.png`。四处漏液位置仍为P03/P06/P13/P18。没有重画PNG，四墙Aseprite仍在r6、地面Aseprite仍在r5。
- 在r4源上复制七个接收面的颜色材质，用世界坐标最近邻采样新颜色图；墙缝、灯槽与地面范围与Godot现行Shader一致。后墙三块共用一张后墙图和同一世界X，不按各块UV拉伸。
- 129个烘焙接收网格、四条独立`ContinuousRibbon_*`原发光面、0个普通灯光。所有几何、位置、UV0/UV2、原灯带颜色／能量和Godot曝光／相机保持。GLB、网格映射和UV2布局文件与r4逐字节一致，Blender源保存后重新打开计算几何／UV哈希也一致。
- CPU Cycles固定1024样本、2048²线性EXR、4px扩边，耗时212.375秒。烘焙DIFFUSE的DIRECT＋INDIRECT，关闭COLOR：接收面的固有色不乘进irradiance，仍由Godot颜色图乘光照；新颜色图会影响漫反射反弹。复用原降噪流程，只处理光照图，不模糊像素颜色图。
- UV2检查17908个有效三角，零退化、越界和正面积重叠；连续后墙图岛与既有扩边保持。没有重新拆岛。

Blender坐标与Godot换算为`Godot=(Blender.X, Blender.Z, -Blender.Y)`。Blender图像UV使用底部原点：地面`U=(X-.2)/20.6,V=(Y-.2)/9.1`，侧墙`U=(Y-.2)/9.1,V=Z/3.4`，前后墙`U=(X-.2)/20.6,V=Z/3.4`。与Godot图像顶部原点的现有采样对应；不能把新1648×728贴图直接塞进旧1680×760图的UV节点。

## Godot使用

拉取main后，F6运行`scenes/dev/room1_surface_lighting_r7.tscn`。默认是当前贴图＋配套r7光照。I比较旧r4／新r7光照；V比较旧r5／修正r6接缝；M墙地模式；N颜色诊断；J回观察点；WASD移动，L沿用灯带开关。正式主入口不变，旧场景均保留。

运行包为`assets/art/room1_surface_lighting_r7/`中的GLB、降噪EXR、映射与manifest，并依赖既有r6墙图、r5地面及Shader。**不要只拖裸GLB当成完整新材质。** GLB是保留UV2的几何载体，内嵌旧颜色图不重写；新贴图由场景Shader绑定。Blender打包工程已包含当前新图及世界坐标节点，可继续编辑源。

Godot沿用r4导入参数：GLB禁用网格压缩以保留UV精度、不生成LOD；HDR不当sRGB、不夹曝光、不生成mipmap。原特殊舱内光Shader保留，只切它们已有的irradiance纹理参数。

## 验证与结果

实际捕获25张比较与17张巡检：六个游戏机位的旧／新光照、N／I恢复、Base Color、raw1024／降噪、四处漏液、四角、真实前墙、门头、两总览和灯开关。图像1280×720、原曝光，无后处理提亮。前墙只在技术图中临时取消`SHADOWS_ONLY`，拍完恢复。

Base Color在两种GI下逐像素一致，N和I往返也一致；旧GI右侧对照与当前独立r6图逐像素一致。灯带开／关／恢复正确，恢复图只在P17动态红屏矩形内有时间差，屏幕外逐像素一致。具体改变像素数／范围见`quality_check.json`，不把动态区域误写成全图精确一致。

新旧线性图在有效区域的平均值约0.207829→0.206973（约-0.41%），属于配套反射的小变化；不是新的增亮方案。raw有采样颗粒，降噪后检查墙角／门头／连续灯槽，没有靠修改颜色图遮盖光照问题。结果只说明本轮数据配套与实际巡检通过，不替代用户对整体美术、主门、人物、玻璃和舱体细节的审查。

## 复现

`scripts/dev/bake_room1_surface_lighting_r7.py`从r4源另建r7，默认拒绝覆盖已有完成EXR。`readback.py`重新打开新源，检查实际图像打包、几何／UV、线性HDR。`capture_compare.gd`和`capture_survey.gd`必须使用正常GL Compatibility实际渲染；headless仅用于导入。

raw EXR留本地，Blender源也打包保留烘焙数据；运行时发布降噪EXR。`readback.py`在没有独立raw文件时读取源工程中已打包的raw图像；比较脚本的raw入口则要求本地重建输出，不将raw、日志、缓存和备份上传。`package_review.py`汇总精确回归与对照页。
