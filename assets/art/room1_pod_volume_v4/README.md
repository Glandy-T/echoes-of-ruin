# 单舱 v4 静态导出

`pod_closed_v4.glb` / `pod_open_v4.glb` 为闭合与45°打开的静态姿态，嵌入八张像素图；保留各材质实际使用UV为TEXCOORD_0。Blender工程保留原运动父级及关键帧，GLB不含运行时开盖动画。

完整源、八份分层Aseprite、来源与验证说明在 `docs/art/experiments/room1_pod_volume_v4/README.md`。Godot独立审图入口为 `scenes/dev/room1_pod_volume_review_v4.tscn`。玻璃的透明/反光表现需使用相应Godot Shader。

仅单舱待审，没有替换整室、改布局或重烘焙Room 1。请勿将候选编号12复制成全室编号。
