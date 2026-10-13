# Room 1 导入资产 r1

适配 Godot 4.6；本机实际使用4.6.2。贴图嵌入GLB，随包 `.import` 设置无损嵌入与最近邻，路径固定在本目录。

| 文件 | 内容 |
|---|---|
| `room1_shell_full_r1.glb` | 墙地、屋顶与占位门；含完整前／左墙和屋顶，没有舱体 |
| `room1_layout_review_r1.glb` | 原剖切范围与20个灰模舱，供核对布局；不要再叠放20个贴图舱造成重复 |
| `pod_closed_v3.glb` | 单舱关闭静态姿态，完整v3贴图 |
| `pod_open_v3.glb` | 原45°开盖终态，静态，不是动画 |
| `nearest_pixel_import.gd` | 只调整这批文件的材质采样；`.import` 已绑定 |
| `pod_placement_godot.json` | 20舱既有位置转为Godot坐标，供后续替换参考 |

请保留 GLB、`.import`、脚本及 `.uid` 的相对关系。如果移到其他项目路径，重新选择 Import Script 路径并重新导入。

所有文件保持米制；房壳根点是外围前左角，舱根点为平面中心。无相机、灯光、碰撞、导航或新增动画。材质已转为 glTF 支持的贴图/PBR表示；Blender 的三档明暗审图 Shader 未迁移。关闭态舱宽1.05m、长约2.294m，实际壳高约0.665m；这是现有资产尺寸，不将其改成工程包络1m高。

[完整学校交接](../../../docs/art/ROOM1_SCHOOL_HANDOFF_20261014.md) / [墙地制作](../../../docs/art/experiments/room1_material_revision_v1/README.md) / [单舱制作](../../../docs/art/experiments/room1_pixellab_pod_trial_v3/README.md)。
