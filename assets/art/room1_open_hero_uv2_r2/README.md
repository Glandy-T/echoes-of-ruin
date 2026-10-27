# Room 1 共享UV2与静态光照 r2

本组文件配套使用：`room1_baked_uv2_r3.glb`、`strip_irradiance_denoised.exr`、`mesh_mapping.json`。替换其中一项而继续读取旧版另外两项，会造成光照落错表面。

修复旧版左墙与四个舱壳的UV2重叠，在临时合并副本上按连续平面展开129个接收网格，形成共享光照图集。颜色UV0、网格轮廓、20舱布局与P12的45°开盖姿态保持。静态光照沿用原四条发光面、64样本和2048图集；人物动态阴影仍由既有运行时Shader处理。

- `uv2_layout_record.json`：烘焙前的有效三角、重叠、越界与UV0保持记录。
- `bake_manifest.json`：实际烘焙参数及GPU后端。
- 当前出仓r3和派生墙地材质小样默认读取本组数据。旧烘焙目录留存作对照。
- 原始未降噪EXR只留本地；运行时使用线性HDR降噪结果。原生像素颜色贴图没有降噪。

可编辑Blender工程、导出读回和同机位画面见 [修复记录](../../../docs/art/experiments/room1_left_wall_uv2_fix_r2/README.md)。重建入口为 `scripts/dev/bake_room1_open_hero_uv2_r2.py`；没有新增PixelLab调用。
