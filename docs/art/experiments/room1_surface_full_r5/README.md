# Room 1 全室墙地 r5

2026-10-27。用户暂时认可r4墙面接缝／旧化，要求推广全墙、增加差分；地面不要接缝，全体做旧，再在少数舱位周围加明确的漏液痕迹。本轮交付为待审全室候选，原r4及之前版本完整保留。

[实际对照与巡检](preview.html) · [独立场景](../../../../scenes/dev/room1_surface_full_r5.tscn) · [运行颜色图](../../../../assets/art/room1_surface_full_r5/) · [校验记录](source/quality_check.json)

## 改动

- 四面墙分别制作完整颜色图：侧墙728×272，前后墙1648×272。主面留白、灯槽沉积、墙脚累积、缝边旧膜、保护带旧接触分层。保持r4中等可见强度，改变轮廓与组合，避免直接平铺局部试段。每面墙8个可编辑层。
- 墙高、灯罩18–35像素行、保护带高度一致。各墙首尾两列共享同一收边，后墙门洞的三块网格按世界X共用整张后墙图。接缝仅由颜色图表达，无新板缝几何。
- 地面统一蓝灰，完整1648×728覆盖20.6×9.1m内净地坪。连续材料色差与边缘沉积，没有地砖网格、十字通道色带或拼接边。保留3层无漏液母版与6层含漏液母版。
- P03、P06、P13、P18四个固定舱位增加旧漏液：从舱底外扩的暗色旧膜、渗染边与断续干涸沉积。四个区域各抽一舱，种子20261027，选择结果固定保存；不在运行中重随机。位置见[manifest](source/floor_manifest.json)和带标注位置图。

液体成分、历史事件和玩法影响仍TBD；不把痕迹与死亡屏幕或人物状态绑定。不增加实时流体、碰撞、湿面高光、设备或几何。

## 可编辑源与复现

`editable/wall_{left,right,front,rear}.aseprite`：各8层；`editable/floor_aged_r5.aseprite`：3层；`editable/floor_leaks_r5.aseprite`：6层。所有图层保持全图坐标，PNG源层也保存在`source/wall_layers/`、`source/floor_layers/`。

1. 用Python/Pillow/NumPy执行`source/build_walls.py`、`source/build_floor.py`生成源层。脚本从当前P01–20场景读取舱位；不导入旧生成器的顶层副作用。
2. 用Aseprite批处理运行`source/package_walls.lua`和`source/package_floor.lua`，生成分层母版并导出运行PNG。Aseprite可通过`--script-param root=...`指定本实验绝对路径。
3. 创建`source/readback/`后运行`source/verify_masters.lua`，重新打开六份母版并独立导出。运行PNG以Aseprite实际合成为准，不用Pillow的1LSB不同舍入覆盖它。
4. 先让Godot导入PNG，再在正常GL Compatibility渲染下执行`capture_compare.gd`、`capture_room_survey.gd`。不要用headless模式代替画面截图。
5. 执行`source/package_review.py`核对母版读回、地图尺寸、转角边列、灯罩像素、r4基线与N往返，生成本页及位置图。截图原图不提亮。

本轮使用项目原创可编辑像素层，不新增AI调用或额度消耗，不把Pixel Canals截图／模型作为生成输入；仅沿用其由颜色图承担结构、灰阶和像素簇的信息组织方法，不宣称原作使用相同贴图尺寸、UV或Shader。

## Godot适配与比较

F6运行`scenes/dev/room1_surface_full_r5.tscn`。M依次比较：0原r4局部基线、1全墙＋旧地面、2全墙＋旧化全地面、3全墙＋旧化地面＋四处漏液（默认）。N切Base Color诊断；J回左侧观察点；WASD移动。Base Color只用于诊断，不是最终自发光设计。

新Shader只装到地面与六份墙网格的颜色材质，继续使用原材质对象供继承照明更新。P02/P12/P17特殊舱内Shader保持；N诊断对其他材质暂存并恢复原Shader参数。前后墙与左右墙均用世界坐标采样，地面只覆盖朝上表面，不改UV0/UV2。

模型、休眠舱、门、人物、布局、游戏相机、灯光与曝光均保持。复用`assets/art/room1_wall_finish_r4/room1_baked_uv2_r3.glb`和`strip_irradiance_denoised.exr`；原Blender源见[已打包r4工程](../room1_wall_finish_r4/room1_wall_finish_r4_packed.blend)，本轮没有模型修改，因此不另存重复Blender工程。新固有色造成的间接反射尚未重新烘焙，本轮不称为新的最终烘焙包。

## 验证边界

实际比较图共19张，包含同机位左／中／右四模式、四个漏液舱基特写、Base Color全室和N恢复；另有14张巡检图。巡检包括前墙、门洞灯带、转角、前后排及全室。游戏剖切会把前墙设成`SHADOWS_ONLY`；只在前墙／转角技术截图中临时设为可见实体，拍后恢复。不能只把相机对准前墙坐标，就把透过隐藏墙看见的全室图当成前墙验收。

精确结果见`source/quality_check.json`与两份`capture_record.json`，不是仅凭脚本退出码判定。独立审查看过四处舱底残迹及同机位对照；母版可见导出、旧基线和N恢复均通过逐像素检查。80 texels/m仅为本次试值；最终尺度、漏液具体设计与全室美术效果仍待用户审图。
