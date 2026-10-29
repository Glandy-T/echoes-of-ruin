# Room 1 一体化主门 v3：房间内效果审查

状态：**可交互的美术审查样本，未定稿**。基于现行 Room 1 → 4F 走廊灰模路线；Room 1 房间、门洞和休眠舱布局未改。

## 本轮调整

- 关闭状态仍是原有尺寸的单扇侧滑门，但门面压回后墙的冷灰绿色和由上至下的应急照明明暗。门下部的保护带分界与后墙墙脚对齐，删除了贴上去一样的亮色外框和大块装饰磨损。
- 独立的四边门洞内侧细灯：待机暗；单人芯片认证成功、允许通行期间持续发绿光。当前 Room 1 无第二通行者，不出现红色门框。猫眼高度小状态窗分别显示暗、黄闪、绿、红。
- 沿用现有 1.37 m × 2.30 m 门叶、约 1.4 m 人员门洞、单扇侧滑运动；门板和碰撞体同步。不新增壁挂认证器、扫描柱或外露把手。

## 可编辑源文件与导入

| 用途 | 文件 |
| --- | --- |
| Blender 主文件 | [`room1_integrated_door_v3.blend`](room1_integrated_door_v3.blend) |
| Blender 重建脚本 | [`source/build_door.py`](source/build_door.py) |
| 128 × 256 像素图层源 | [`editable/door_front_v3.aseprite`](editable/door_front_v3.aseprite) |
| 图层生成脚本 | [`source/build_pixel_layers.py`](source/build_pixel_layers.py) |
| Godot 使用的像素贴图 | [`../../../../assets/art/room1_integrated_door_v3/door_front.png`](../../../../assets/art/room1_integrated_door_v3/door_front.png) |
| Godot 使用的 GLB | [`../../../../assets/art/room1_integrated_door_v3/room1_integrated_door_v3.glb`](../../../../assets/art/room1_integrated_door_v3/room1_integrated_door_v3.glb) |
| Godot 审图场景 | [`../../../../scenes/dev/room1_integrated_door_v3.tscn`](../../../../scenes/dev/room1_integrated_door_v3.tscn) |

Godot 打开审图场景即可看自动感应、门板侧滑及由 Room 1 走到 4F 走廊。导入时保留 GLB、PNG、脚本和场景的仓库相对路径；GLB 内也打包了该贴图。Aseprite 三图层输出与运行时 PNG 的逐像素回读一致。门面使用 UV0 和最近邻采样，灯语是 Godot 运行时材质，不烘进像素贴图。

## 审图与验证

[打开五状态对比页](preview.html)：相机和分辨率均为 Godot 实拍 1280 × 720。保留一张反馈前的关门截图用于同机位对照。

[`runtime_validation.json`](runtime_validation.json) 的 Godot headless 检查结果为 `PASS`：黄闪、四段门框、授权开门、碰撞同步、角色走出门洞、离开后复位及拒绝时仅小窗发红。此检查只覆盖一名角色，不证明尾随防护、安全避夹或停电解锁。

## 仍需审查

- 门洞外的 4F 走廊仍是辨识灰模。本审图场景临时压低了入口墙、地面和对面锁闭占位门的预览亮度，避免开门时出现亮灰矩形；这不决定走廊的最终配色、材质或灯光。
- 门面与后墙的对接已按当前 Godot 室内镜头修正，但其他镜头、正式动态光照和不同灯带状态仍需后续查看。
- 本轮曾试用 PixelLab 生成一张门材质候选，结果偏恐怖片式机械格栅，已明确弃用，未进入最终贴图或 GLB。本版为可编辑的人工控制像素图层，不把那张生成图冒充已通过审查的素材。
