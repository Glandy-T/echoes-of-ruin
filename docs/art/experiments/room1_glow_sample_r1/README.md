# 屏幕与舱窗荧光近景小样 r1 — 2026-10-14

用户认为上轮灯带不明显、屏幕和玻璃透光很假，想要荧光感。**上轮室内照明候选不通过。** 用户同意先做一个屏幕与一个舱窗近景，把自身发光、光晕与附近受光分开比较。本轮只点亮P12，不把小样直接铺到20舱，也不改亮舱设定。

## 查看

打开 `scenes/dev/room1_glow_sample_r1.tscn`，F6运行：1屏幕、2舱窗、3整舱、4室内预览；N开启／关闭Glow、P开启／关闭附近投光、B屏幕电源、G舱内光、L原灯带候选、H说明。近景镜头固定，不用于测试人物运动。

## 屏幕

沿用原像素UI贴图，发光乘算能量2.0，颜色偏灰蓝白，黑底与字形区分保留。Glow独立处理边缘光晕，附近小范围受光单独由局部光提供（能量0.012、范围0.5m）。屏幕设为显示层4，投光只影响层1的外壳与环境，避免局部灯反照屏幕制造亮点。

## 舱窗

玻璃改为普通Alpha透明材质（alpha0.2、roughness0.3），不再使用Alpha Depth Prepass，也不加载原不透明像素反射图；玻璃本身不发光。前轮复制玻璃网格的窗后发光衬面隐藏。

将透窗光代理移到原模型实际舱内、离地0.45m处，能量0.16、范围1.15m、开启阴影，照亮已有内部结构。玻璃用层2、局部光只作用层1，避免“窗面被点光照出一个圆斑”。实际近景可以透过窗面看到舱内结构和冷色受光；P关掉舱内光后仍可辨透明结构，玻璃不是发光板。

这不是完整玻璃光学模拟：未实现真实折射、焦散、动态反射或人物；舱内点光是照明候选，未定义真实灯具位置。玻璃颜色、厚度、反射与荧光强度仍需审图。

## 光晕与验证

使用Godot 4.6.2现有GL Compatibility，不切换全项目渲染模式；Environment开启Glow，候选Intensity0.4、Threshold0.5、HDR Scale1.0、Bloom0.0。未通过全屏Bloom把整个房间模糊化。基础环境光暂为0.22，便于近景辨认外壳。

保存7张真实1280×720截图：屏幕Glow开／关、舱窗Glow开／关、舱内投光关、整舱、室内预览。对同镜头、同材质的开关图做像素差分（排除说明区域），验证Glow及舱内光确实改变渲染；另检查玻璃不发光、透明模式和旧衬面隐藏，见 `validation.json`。

已目视检查屏幕字形、光晕、透明窗面和内部受光。技术验证只说明效果实际生效，荧光美术观感仍待用户判断；灯带最终照明未在本轮重新制作。旧照明候选与源GLB／贴图保留。

源：`scripts/dev/room1_glow_sample.gd`、`build_room1_glow_sample.gd`、`validate_room1_glow_sample.gd`。生成脚本从旧照明场景另存新版本；验证命令为Godot控制台 `--path . --script res://scripts/dev/validate_room1_glow_sample.gd --resolution 1280x720 --quit-after 360`。

依据：[Godot 4.6 Environment Glow](https://docs.godotengine.org/en/4.6/classes/class_environment.html#class-environment-property-glow-enabled)。Compatibility支持Glow，但部分参数无效；本轮没有使用不支持的Levels／Blend Mode来宣称效果。
