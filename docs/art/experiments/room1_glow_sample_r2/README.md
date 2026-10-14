# 像素玻璃与屏幕荧光小样 r2 — 2026-10-14

用户认为 r1 舱窗透光方向可以，但原像素玻璃消失；屏幕光晕仍显方块。r2 恢复像素反光并减弱屏幕边框发光。用户要求先审小样、暂不上传，本轮仅保存在本地，尚未美术验收。

打开 `scenes/dev/room1_glow_sample_r2.tscn`，F6运行。1屏幕、2舱窗、3整舱、4室内；V切换像素反光、N切换光晕、P切换附近投光、B屏幕电源、G舱内光、H说明。

玻璃使用原GLB的像素反光贴图，最近邻采样；按贴图明度调整透明度，底色alpha 0.14、亮反光最高0.68，让像素反光与透窗所见的内部结构同时存在。保留 r1 舱内照明、普通Alpha混合与隐藏的旧发光衬面。反光纹理是原有绘制表现，不是实时环境反射；弱EMISSION补偿只用于保持纹理可读，玻璃不作为照亮房间的灯具。

屏幕保留原像素UI，以文字及状态条的亮度驱动发光，沿UV边缘平滑降低发光权重，避免整个边框同样明亮。仍使用原Environment Glow与独立局部投光；矩形屏幕及原贴图中的横线仍会影响光晕轮廓，未声称完全消除矩形形状。

保存7张实际1280×720截图：屏幕光晕开／关、玻璃像素反光开／关、舱内光关、整舱、室内。验证实际生效的两个Shader覆盖，以及同镜头的光晕、像素反光、内部受光差分，结果见 `validation.json`。已目视检查屏幕和舱窗近景；技术验证说明效果生效，最终观感待用户审查。

源文件：`scripts/dev/room1_glow_sample_r2.gd`、`room1_pixel_transparent_glass.gdshader`、`room1_screen_soft_emission.gdshader`、`build_room1_glow_sample_r2.gd`、`validate_room1_glow_sample_r2.gd`。原GLB、PNG和r1场景保留；只试P12，没有推广到20舱，也未重新处理灯带或主角物理。

材质依据：[Godot 4.6 Spatial Shader](https://docs.godotengine.org/en/4.6/tutorials/shaders/shader_reference/spatial_shader.html)。
