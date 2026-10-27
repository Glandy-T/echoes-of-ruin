# Room 1 高采样光照 r3

当前r3及墙地小样使用。GLB、网格映射与UV2记录逐字节沿用 `room1_open_hero_uv2_r2`；灯光参数不变，固定1024样本重烘焙，减少墙角噪声降噪形成的波纹。

配套读取 `room1_baked_uv2_r3.glb`、`strip_irradiance_denoised.exr`、`mesh_mapping.json`。参数见 `bake_manifest.json`，实际画面、范围及已知美术待办见[本轮说明](../../../docs/art/experiments/room1_corner_quality_r3/README.md)。原始EXR不上传；打包Blender和生成入口保留。
