# Room 1 P12 v4 / 实际受光接入 v5

`pod_closed_v5.glb`及`pod_open_v5.glb`保留v4几何／颜色图，新增各自独立的LightmapUV；父级应放在Godot `(3.525,0,-7.65)`，不再叠加第二次世界平移。

`closed_irradiance.exr` / `open_irradiance.exr`为相应姿态的不透明舱体接收现有房间四条灯带的线性HDR光照。两个姿态不能混用光照图。玻璃／显示屏不在此接收光照中，分别使用透明与发光Shader。

房间其余部分仍为r9原GI；这是P12局部检查，不是完整闭合场景全室新烘焙。Godot运行入口 `scenes/dev/room1_pod_room_v5.tscn`。源工程、检查截图与限制见 `docs/art/experiments/room1_pod_room_v5/README.md`。八份像素母版保持上一轮 `room1_pod_volume_v4/editable/`。
