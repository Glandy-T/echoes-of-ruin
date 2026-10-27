# Room 1 局部材质小样 r1

本目录两张PNG只供 `scenes/dev/room1_surface_sample_r1.tscn` 使用，不替换原GLB材质。

- `wall_sample.png`：128×136，左墙z=-6.4..-3.2m、高0..3.4m，暖灰矿物／工程复合面层。
- `floor_sample.png`：128×128，x=.2..3.4m、z=-6.4..-3.2m，统一蓝灰连续复合地坪。

最近邻，PNG无损、无mipmap。40 texels/m是当前局部试值，不是项目标准。Shader仅混合固有色，保留原UV2烘焙和胶囊阴影；没有增加几何或接缝。

[审图与来源](../../../docs/art/experiments/room1_surface_sample_r1/README.md)；Aseprite母版、原创导图、原始PixelLab输出与实际提示词均在该实验目录。两个任务各10次额度，共20；没有将Pixel Canals截图／贴图作为AI输入。
