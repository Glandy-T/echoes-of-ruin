# Room 1 → 4F 西侧走廊 → 1F 西消防梯间：可通行灰模 v3

本版把现有 Room 1 的 **Godot 游玩审查场景**接到上一版整栋楼灰模的 4F 西南分区人员走廊和西消防梯，保留 Room 1 模型、贴图、舱位和主角现有 2D 占位。它是独立的可玩路线测试场景，不替换游戏主入口，也不确定主门、楼梯间灯光或最终镜头设计。

## 依据和边界

- 平面尺寸、房门和消防梯位置沿用冻结的 [`v3_trim/floor_layout.json`](../../../cad/cryo_standard_floor/v3_trim/floor_layout.json) 与现行[楼体 Brief](../../CRYO_BUILDING_LOWPOLY_BRIEF.md)。`SW-01` 仍只是可替换的技术锚点，不是最终叙事房号。
- 路线美术源自独立 Blender 灰模 [`cryo_building_stairs_v2.blend`](../cryo_building_stairs_v2/cryo_building_stairs_v2.blend)，由 [`source/export_room1_west_route_v3.py`](source/export_room1_west_route_v3.py)裁出 Room 1 门外至西梯的必要几何，导出到 `assets/art/cryo_building_room1_route_v3/room1_west_route_v3.glb`。FreeCAD 只提供工程位置关系，没有直接把 CAD 网格作为游戏模型。
- Room 1 背墙和门仍由现有场景提供；路线灰模从该墙外缘开始，避免重复覆盖原有墙、地和灯带。其余房间和非授权楼层室内没有实例化。
- 其他门保留锁定占位；人员电梯不接入。1F 室外出口的位置仍待核定，路线到 **1F 西梯间平台**即止。

## 在 Godot 查看

在 Godot 4.6.2 中打开 `scenes/dev/cryo_building_room1_route_v3.tscn`，运行当前场景（F6）。主角靠近 Room 1 主门并等待扫描，门会沿用此前的芯片测试逻辑开启。WASD 移动；F1 到门外走廊、F2 到 4F 西梯入口、F3 到 1F 西梯间，便于快速审图；U 切换测试芯片、R 回房间、H 隐藏说明。F1～F3 是审查场景的跳转键，不属于正式游戏交互。

Godot 场景只加载这条可走路线：4F 授权西南走廊以及西梯的 4F、3F、2F、1F 梯段。其余三座消防梯仍保存在完整的 [v2 Blender 工程](../cryo_building_stairs_v2/README.md)中，本版没有将整栋楼加载进游玩场景。

新区域使用**仅供灰模审图的中性无光照材质**，使走廊和楼梯在尚未设计灯光时也能辨认。Room 1 原有材质和烘焙照明未修改。消防梯采用临时的近距离跟随镜头，避免低楼层墙体挡住主角；正式楼梯镜头仍需单独确定。

## 验证与截图

- [Godot 实际截图并排查看](preview.html)：开门连接、4F 走廊、西梯入口、1F 平台和楼梯结构俯视。俯视图只供结构审查，不代表最终游戏镜头。
- [完整物理验证结果](physics_validation.json)：`PASS`、`errors=[]`。脚本使用现有 `CharacterBody3D` 等待芯片扫描开门，实际走出房间、经过 4F 走廊、沿西梯下降三层至 1F 平台；4F→3F→2F→1F 的平台高度依次约为 `-3.8m / -7.6m / -11.4m`。门外、梯前、4F 和 1F 平台射线均命中路线碰撞体。
- 复测场景：`scenes/dev/cryo_building_room1_route_v3_verify.tscn`。命令：`Godot_v4.6.2-stable_win64_console.exe --headless --path . --quit-after 16000 res://scenes/dev/cryo_building_room1_route_v3_verify.tscn`。
- 截图场景：`scenes/dev/cryo_building_room1_route_v3_capture.tscn`。截图脚本需要带图形窗口运行；Godot headless 的空视口无法产生图片。

## 后续待定

主门目前仍继承旧的自动识别滑动占位实现，**不是**最新的[一体化门体与黄绿红通行灯语 Brief](../../ROOM1_INTEGRATED_DOOR_ACCESS_BRIEF.md)的实现；临时扫描线也不代表定案。门的造型、开闭美术、其他门的权限反馈、楼梯间照明、正式镜头、楼梯扶手、材质和像素贴图都未定。1F 到室外的路线必须先依据更新后的建筑图核定，不能把本次抵达 1F 梯间当作已经抵达室外。主角最后会换成低模 3D＋像素贴图；当前 2D 纸片仅保留为运动与比例占位。
