# Room 1 一体化主门 v3：房间内效果审查

状态：**可交互的美术审查样本，未定稿**。基于现行 Room 1 → 4F 走廊灰模路线；Room 1 房间、门洞和休眠舱布局未改。

## 本轮调整

- 关闭状态仍是原有尺寸的单扇侧滑门。门面直接取自 Room 1 现行 r6 墙面材质的一块无接缝区域，保持相同的矿物色阶、像素密度、大面变化和下缘沉积轮廓；只增加滑动密封边与小状态窗。不再另画一套平滑渐变或随机污斑。关门时隐藏未点亮的门框灯槽；门叶不延续墙脚保护带。
- 独立的四边门洞内侧细灯：待机暗；单人芯片认证成功、允许通行期间持续发绿光。当前 Room 1 无第二通行者，不出现红色门框。猫眼高度小状态窗分别显示暗、黄闪、绿、红。
- 沿用现有 1.37 m × 2.30 m 门叶、约 1.4 m 人员门洞、单扇侧滑运动；门板和碰撞体同步。不新增壁挂认证器、扫描柱或外露把手。
- 后墙原有约 20 cm 厚，门叶已在墙体深度内。此前尝试从门洞两侧拉接缝至天花板，形成了像“耳朵”的竖线，已撤销。现在沿用 r6 原墙全部分板节奏，门位于原有两条接缝之间的宽面板内；仅清除穿过门楣中央的旧接缝。没有增加门洞装饰框，也未改变墙体尺寸、门洞或 UV2。

## 可编辑源文件与导入

| 用途 | 文件 |
| --- | --- |
| Blender 主文件 | [`room1_integrated_door_v3.blend`](room1_integrated_door_v3.blend) |
| Blender 重建脚本 | [`source/build_door.py`](source/build_door.py) |
| 112 × 184 像素图层源 | [`editable/door_front_v3.aseprite`](editable/door_front_v3.aseprite) |
| 后墙门洞模块图层源 | [`editable/wall_rear_portal.aseprite`](editable/wall_rear_portal.aseprite) |
| 图层生成脚本 | [`source/build_pixel_layers.py`](source/build_pixel_layers.py) |
| Godot 使用的像素贴图 | [`../../../../assets/art/room1_integrated_door_v3/door_front.png`](../../../../assets/art/room1_integrated_door_v3/door_front.png) |
| 后墙门洞模块贴图 | [`../../../../assets/art/room1_integrated_door_v3/wall_rear_portal.png`](../../../../assets/art/room1_integrated_door_v3/wall_rear_portal.png) |
| Godot 使用的 GLB | [`../../../../assets/art/room1_integrated_door_v3/room1_integrated_door_v3.glb`](../../../../assets/art/room1_integrated_door_v3/room1_integrated_door_v3.glb) |
| Godot 审图场景 | [`../../../../scenes/dev/room1_integrated_door_v3.tscn`](../../../../scenes/dev/room1_integrated_door_v3.tscn) |

Godot 打开审图场景即可看自动感应、门板侧滑及由 Room 1 走到 4F 走廊。导入时保留 GLB、PNG、脚本和场景的仓库相对路径；GLB 内也打包了该贴图。Aseprite 三图层输出与运行时 PNG 的逐像素回读一致。门面约 80 texel/m，与原墙相同；基础图取自 r6 后墙贴图的 x=956–1068、y=65–249 无接缝区域。门面使用 UV0 和最近邻采样，灯语是 Godot 运行时材质，不烘进像素贴图。

后墙新图以既有 r6 最终 PNG 为底图，仅清除门楣正中旧缝 x=812–819、y=44–80；**其余像素、分板接缝、灯带与墙脚逐像素保持原样**。原墙接缝 x=688、944 构成约 3.2 m 宽的门所在分板。该图 Aseprite 重开导出与运行时 PNG 逐像素一致。

## 审图与验证

[打开五状态对比页](preview.html)：相机和分辨率均为 Godot 实拍 1280 × 720。保留“耳朵”接缝、旧门面及门缝修改前的同机位截图用于对照。

[`runtime_validation.json`](runtime_validation.json) 的 Godot headless 检查结果为 `PASS`：三段后墙均使用新门洞模块图、黄闪、四段门框、授权开门、碰撞同步、角色走出门洞、离开后复位及拒绝时仅小窗发红。此检查只覆盖一名角色，不证明尾随防护、安全避夹或停电解锁。

## 仍需审查

- 门洞外的 4F 走廊仍是辨识灰模。本审图场景临时压低了入口墙、地面和对面锁闭占位门的预览亮度，避免开门时出现亮灰矩形；这不决定走廊的最终配色、材质或灯光。
- 门面与后墙的对接已按当前 Godot 室内镜头修正，但其他镜头、正式动态光照和不同灯带状态仍需后续查看。
- 本轮曾试用 PixelLab 生成一张门材质候选，结果偏恐怖片式机械格栅，已明确弃用，未进入最终贴图或 GLB。本版为可编辑的人工控制像素图层，不把那张生成图冒充已通过审查的素材。
