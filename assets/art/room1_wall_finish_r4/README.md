# Room 1 墙面与灯槽 r4

当前出仓r3及派生小样默认使用。修前墙内面颜色UV0，将三段后墙内面接为连续光照坐标，1024固定样本配套重烘。几何位置／法线／节点／原生图像与映射保持；灯光发光面参数保持。

配套使用 `room1_baked_uv2_r3.glb`（沿用兼容文件名）、`strip_irradiance_denoised.exr`、`mesh_mapping.json`。manifest中的 `uniform_strip_emission` 与 `diffuser_radiance_scale` 控制Godot发光面，防止再次叠加分块GI。新UV2禁止套旧HDR。

[可编辑源、实际对照和完整检查](../../../docs/art/experiments/room1_wall_finish_r4/README.md)。
