# 暗房与连续灯带烘焙 r3 — 2026-10-14，本地待审

用户暂时保留屏幕r4，要求整体房间更暗、灯带来源更清楚，并指出旧填光没有渐变或阴影。分段点光试验r2又出现灯泡状光斑，用户明确否定。r3不再用点光或聚光模拟灯带：以四整条连续发光面烘焙房间与舱体的静态照明。

## 查看

打开 `scenes/dev/room1_lighting_continuous_bake_r3.tscn`，F6运行。WASD移动比例标记；1中央、2左、3右、4前、5后、6～9四角，R复位，T标记，H说明。L同时切换灯带可见发光与它的整张光照图；G舱内灯、B屏幕、N屏幕光晕。默认试P02/P12/P17三亮、其余熄灭，编号仍可调整，非剧情定案。

环境底光从近景小样的0.22、旧全室候选的0.12降为0.025。旧方向光／稀疏点光关闭，旧Shader连续但无阴影的均匀填光能量为0。灯带自身可见发光候选0.7，烘焙接收能量1.2；没有为灯带创建Point/Spot代理。舱内和屏幕仍使用各自小范围局部灯，这是设备自身的投光，不承担灯带照明。

## 烘焙来源

Blender 5.0.1 / Cycles，4个连续长条发光面，宽0.06m，高度3.05m，沿前／后／左／右墙，发光能量20；零灯光对象。原房壳、20舱实体参与遮挡，烘焙129个不透明接收网格的Diffuse Direct＋Indirect，排除Albedo，64 samples、2漫反射反弹、2048²共享UV2图集。透明窗和显示面不当作不透明挡板。

Blender原生Compositor Denoise处理HDR光照图，输出单层RGB ZIP EXR；像素颜色贴图不降噪。Godot中的接收Shader分别用原UV0最近邻颜色和UV2线性光照图，保留像素颗粒及连续照明。左墙UV0偏移在这份烘焙副本中修正，原GLB／PNG不改。

素材副本在 `assets/art/room1_continuous_bake_r3/`：`room1_baked_uv2_r3.glb`、`mesh_mapping.json`、`strip_irradiance.exr`（原始光照）、`strip_irradiance_denoised.exr`（运行用光照）、`bake_manifest.json`。原始大EXR仅用于本地再降噪，应在后续交付时决定是否作为制作源一起上传；本轮没有上传任何文件。

原GLB中两份内舱网格分别为`pod_v3_interior`及`pod_v3_interior.001`，Godot将句点转下划线；映射保留两者，避免把第二份漏掉或覆盖到第一份。运行用图已核实为2048²、B/G/R通道，并实际导入；失败的多层EXR不是最终成果。

## 验证与限制

8张真实1280×720截图包含中央、只有舱灯、全部关闭、只有灯带、左／右／后侧和人物比例标记。129个实际接收网格均有UV2，灯带Point/Spot数量0，光照图与关灯差分通过。中央墙面固定采样区域中，上部亮度0.1632，下部0.1359，确认更靠近灯带的区域更亮；已目视检查整体、左侧及无点状光斑的墙面。技术验证不等于美术验收。

这是静态烘焙照明：房间／舱体遮挡已进入光照图，改变布局需要重烘焙。主角移动阴影、开盖后阴影更新与动态光照探针尚未实现；比例标记只用于相机测试。不要把本场景称为完成主角物理或最终照明。玻璃保留像素反光与透光方向，在暗房中移除纹理的额外自发光补偿，像素接缝仍待后续。屏幕沿用r4核心与柔化光晕，推广到三亮舱。

主场景、项目渲染模式与原资产未改；旧版本及失败r2记录保留。本轮只本地保存，沿用用户“先审小样，暂不上传”。

重建：Blender后台先执行 `scripts/dev/bake_room1_continuous_strip_r3.py`，再执行 `denoise_room1_strip_r3.py`；Godot导入后执行 `build_room1_lighting_continuous_bake_r3.gd` 与 `validate_room1_lighting_continuous_bake_r3.gd`。本版自带烘焙UV2与接收Shader，没有使用Godot LightmapGI节点。Godot原生LightmapGI资料仅用于确认烘焙照明与动态阴影的区分：[LightmapGI](https://docs.godotengine.org/en/4.6/classes/class_lightmapgi.html)。
