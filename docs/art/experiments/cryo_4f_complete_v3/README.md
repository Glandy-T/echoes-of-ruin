# 4F 整层外壳与走廊 v3

**2026-11-04实机修正v4：** F6仍运行 `scenes/dev/cryo_4f_complete_v3.tscn`。遮挡状态保留42%不透明度及双面原墙纹理；门仅按真实人物视线淡化，走近对门不会单独改变透明度。其他运行中认证门改为E触发小窗黄闪→红灯拒绝→待机，不再弹权限不足文字框。门后灰色场景留待后续。最新对照：`docs/art/experiments/cryo_4f_feedback_v4/preview.html`（仓库根路径），功能回归通过。

2026-11-04，独立F6候选：`scenes/dev/cryo_4f_complete_v3.tscn`。[实机审图](preview.html)。按用户要求，其他47间不制作休眠舱或可进入室内，只保留墙体／门／遮挡透明轮廓。Room 1沿用r30及既有20舱。正式F5仍r19，此版本待用户审看空壳方案。

## 场景范围与操作

- 冻结依据：`docs/cad/cryo_standard_floor/v3_trim/floor_layout.json`，48房间、8走廊、侧廊与连接节点；429烘焙接收面，430外壳／门体。没有复制47套室内舱体。
- 墙继续复用r24，地坪复用r26中央过道裁片，不含舱位印痕；门沿用r30。新增PixelLab额度0次，原像素颜色图不降噪、不重画。
- 邻室墙／门楣／门体遮挡镜头时降至12%透明；离开后恢复，碰撞始终有效。增加上部探针，避免墙身透明但门楣挡镜。只测试此空壳方案，未制作其他房间室内。
- 首次E开始认证，认证后门开，黑门洞显示「E：廊下へ／休眠室へ」。第二次E触发0.22秒淡出，全黑时换位并转向180°，停0.08秒后0.30秒淡入。门洞双面黑色，行走碰撞不能绕过交互边界。
- 其他房门／防火区门保持现有权限锁定，E有拒绝反馈；电梯停用。F12只是技术切区，不授予通行权限，也不改剧情。
- F7透明对照，F8门外，F11整层总览，F12四区审查，F9灯带，F10 raw／降噪。WASD按当前镜头方向移动。

## 配套烘焙与数据

Cycles CUDA，4096样本，1491.75秒；DIRECT＋INDIRECT DIFFUSE，COLOR关闭；4总反弹／3漫反射，黑色世界，顶棚仅参与烘焙。颜色最近邻采样，照度线性采样，能量1.2；灯带独立显示，六个临时Omni保持关闭。处理方法沿用室内。

整层4096²图集，光照16px/m，颜色80px/m。局部v2光照120px/m，并非本层参数。先保存独立面图岛的Cycles原始raw和denoised，再以世界共面坐标分别双线性重投影到148个连续平面；不重画材质、不对raw降噪。`strip_irradiance.exr`是未降噪输出的UV2重参数化结果，**不是未经重采样的原始文件**；未经重投影的结果保留为`source_*.exr`，原始UV工程／映射／GLB同时保留。最终及原始EXR均为线性16-bit half-float ZIP。

连续共面墙身／门楣、整层地坪使用共享仿射坐标。858有效三角，零正面积重叠／退化／越界；244共享顶点一致。图岛矩形实测最短16px，四像素扩边后理论剩8px。导出的GLB重新导入校验UV2、映射边界及SHA；HDR有限非负且非空。报告：`continuous_uv_validation.json`、`bake_validation.json`、资产目录`manifest.json`。

Runtime裁掉跨越Room 1的三个长壳体`Shell_W001/W016/W017`的室内部分，并隐藏重复`Header_D001`；已有r30房墙是该室内唯一表示。外侧接收面与烘焙几何保持，未通过透明改变碰撞。原封闭边界仍留在Blender烘焙上下文。

## 实际检查与边界

`functional_validation.json`通过：不靠近自动认证、两次E、黑屏下换位、门洞行走阻挡、返回、SW第一整条走廊／第二走廊连接、相邻房门及内部门禁、16个步行区域的地面碰撞、临时灯关闭。北区与东区以地面射线、技术切区和画面取证覆盖，未声称正常玩法已解除区域锁。

实机1280×720，九个游戏机位raw／降噪、六个门状态、透明开／关／恢复、整层总览。另拍八走廊双侧各八段重叠技术墙面及四段地面，320张技术原图；技术相机与墙体恢复仅在捕获脚本生效。已检查联系表、代表原尺寸墙脚／灯槽／门洞、转角和地面，未见新增三角切割／大块串色。raw有细碎采样起伏，默认降噪更平滑；不以4096采样或UV报告当作用户视觉认可。

空房区域没有地板／舱体，只显示透明墙壳；灰色背景会在剖切前景出现。楼梯入口使用已有灰盒（西楼梯路线保留，东南北导出4F入口），楼梯美术、电梯专用门面、公共区细节和正式3D人物均待后续。临时纸片角色沿用室内受光，未做新动态照明。正常游戏入口未迁移，整层是可检查的候选，不代表整栋建筑或所有功能已完成。

## 重建

从仓库根运行，需Blender5.0（Cycles），Godot4.6.2，以及Pillow供预览联系表：

1. `blender --background --python docs/art/experiments/cryo_4f_complete_v3/source/export_other_stairs.py`
2. `blender --background --python docs/art/experiments/cryo_4f_complete_v3/source/build_and_bake.py`
3. `blender --background --python docs/art/experiments/cryo_4f_complete_v3/source/continuous_atlas.py`（只能在新建原始烘焙后运行一次）。
4. `blender --background --python docs/art/experiments/cryo_4f_complete_v3/source/audit_bake.py`
5. Godot导入，运行`cryo_4f_complete_v3_verify.tscn`、`cryo_4f_complete_v3_capture.tscn`、`cryo_4f_surfaces_v3_capture.tscn`；捕获需要图形渲染。
6. `python docs/art/experiments/cryo_4f_complete_v3/source/make_review.py`。

可编辑源`cryo_4f_complete_v3.blend`，原UV源`cryo_4f_original_uv.blend`。贴图依赖仓库相对路径。退出验证时有继承场景的ObjectDB泄漏警告，功能断言通过；尚未把该退出警告定位为本次新增或既有问题。
