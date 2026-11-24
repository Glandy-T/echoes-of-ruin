# R5 区域平涂 · 阶段一审图

[中性光三角度并排](neutral_compare.png) · [Room 1 站立、行走并排](room_compare.png) · [带动作的 GLB](walk_pixel.glb) · [可编辑 Aseprite](flat.aseprite) · [128 图集](skin.png)

基线为上一版 R5 头部小样 V3，身体沿用初版 PixelLab 贴图。本轮全程没有生成。服装取自 B_original 的主色 #E7DFCF，领口、袖口、下摆仅用一档 #BEB6A7。肤色 #EAC19D，头发 #313B3A 与 #454E48。脸部是单独的 Aseprite 图层，逐点指定 B 原脸的上眼睑、鼻口和淡阴影，保留对齐后的脸部 UV。

按同一网格的解剖区域分出衣身及头颈、头发、四肢三个渲染表面，各自对 128 图集作边缘扩色，以免邻岛在发尖和袖口串色。三个表面共用原有顶点属性、UV、蒙皮和动画。衣身没有褶皱暗纹；可见的体积和下摆厚褶来自网格、法线与照明。source/regions.py 准备区域底色和扩边，source/face.lua 在 Aseprite 指定原生像素，source/package.py 装配 GLB。

Blender 使用相同的中性工作室光、关镜面高光，正面、斜侧、右侧各自对齐前后机位。Godot 4.6.2 以 Room 1 原光、1.4025 米角色高度、1280×720、最近邻截取静止和原 walk 的第 21 帧。并排使用相同像素裁切。正式场景未替换，暗处五官仍较难辨认。

原尺寸实机：[原站立](before_room_stand.png) · [新站立](after_room_stand.png) · [原行走](before_room_walk.png) · [新行走](after_room_walk.png)。
