# 标准休眠舱 v8：统一源、真实动画与碰撞

本轮落实已确认双侧灯管，并完成单舱可复用场景；未推广20个舱，未替换正式游戏入口。

## 打开与审查

- Godot房间入口：`scenes/dev/room1_pod_standard_v8_review.tscn`，F6运行。
- 可复用单舱：`scenes/props/cryopod_standard_v8.tscn`，作为实例加入其他场景；自身不附带房间或相机。
- [Blender统一母版](room1_pod_standard_v8_packed.blend)：完整舱体、内侧灯管、像素图、UV0/LightmapUV与LidOpen动作。
- [开合、动画逐帧与独立控制对照](preview.html)。所有截图为实际Godot输出，不作后期提亮。

房间O开／关盖，R从闭合重播开盖，G内侧灯管，B屏幕，L墙灯，J回观察点，WASD移动。P12使用标准舱，其余19舱沿用原版本。原P12旧大盒／静态开盖碰撞撤销，由标准舱碰撞接管。

## 源模型与动画

保留已确认v4外形、尺寸、玻璃曲面厚度和八张像素图。灯管实体及窄壳已并入Blender和GLB，固定在壳体两条内侧长边；不再仅为Godot临时盒组件。灯管发光／受光与屏幕仍由Godot分别控制，P12旧中央Omni关闭。

玻璃、盖内衬、内腔、显示屏等均为真实网格，按实际材质使用的颜色UV统一为`UV_GODOT_0`。每个网格恰有两套UV：UV0颜色、UV2光照。玻璃或内腔不以空节点冒充实际分件，显示器背壳不按“display”模糊匹配误当屏面。

单个GLB导出真实`LidOpen`动作，Godot长度约2秒：先垂直抬升12cm，再侧移／转动，保留既有45°终态。source帧1闭合、帧20抬升、帧60打开。不是两个静态模型替换，也不重新自由设计外轮廓。可以中途反向；采样路径的盖体与固定壳／床／灯管未见三角相交。

## 碰撞与控制

固定壳、床面和移动盖分别有物理碰撞。固定壳用实际三角面保留内腔；盖的碰撞随动画移动。默认角色检测使用layer 2，空舱可关盖，活动CharacterBody占住舱口时会阻止或反向打开。此项是避免夹入的技术保护，可通过`closing_blocker_check`与mask配置，不定义新的世界观规则或自动门机制。

物理实测包括关盖阻挡、开盖入口净空、实际CharacterBody落稳床面、移动盖碰撞随动、中途反向、关盖终态／结束信号及占用保护。两实例的灯管、屏幕数据与动态文字纹理相互独立；详细结果见`runtime_check.json`，不以“有CollisionShape”代替实际接触测试。

常用API：

```gdscript
pod.request_open()
pod.request_close()
pod.toggle()
pod.set_tube_powered(true)
pod.set_screen_powered(false)
pod.set_screen_state("----", "----", 0.0, 0.0, 0.0)
pod.set_pose_lightmaps(closed_map, open_map, 1.2)
```

状态为closed/opening/open/closing；信号有started、finished、state_changed和screen_changed。`set_open_immediate`、`set_open_progress`供初始化／审图，不是正常关盖占用保护入口。镜头／移动方式不由单舱控制器管理。

屏幕保留128×48原设计框架，使用项目DotGothic16字体在原文字栏显示姓名／状态，三个进度条分别设置。默认均为占位数据；示例TEST/STANDBY仅用于技术演示，不是人物设定。文字先清理原占位区域再覆盖，进度条替换原填充而非与固定旧条叠加。`get_screen_texture()`返回底图，`get_screen_overlay_texture()`返回每实例独立文字层；房间光晕同步这两者和进度。

根据用户对纯黑屏幕背景的反馈，通电背景改为低亮度蓝灰底光（实例默认`tint=#526C76, energy=0.8`）。字形／进度条发光保持，背景不加入房间光晕提取，避免整块屏幕变成光牌；关机背景不发光。该值是此单舱参数，不是全项目调色标准。`set_screen_background(tint,energy)`可独立调节。对照页保留同机位纯黑参考、蓝灰背景和开盖脚端内部检查。

## 光照边界

18个网格共用一次打包的LightmapUV；闭合／打开两张图使用相同UV布局。P12端点光照沿用r9实际房间四条灯带和其他物件遮挡，灯管局部受光继续用已确认v7分布式近似，防止重复计算发光。运行时按开盖进度混合两张线性HDR，途中属于端点插值，不是每帧新路径追踪。

该光照只适用于P12位置。把prefab放到其他位置时，需要外部传入对应位置的光照；无图时不会用白纹理假装已烘焙。其余19舱和墙地GI保持，周边地面对新盖的动态静态投影仍需后续全室整合处理。地面r9仍是此前搁置方案，主门、人物和全项目像素规格没有因此定案。

## 验证与复现

`source/build_standard_v8.py`生成模型与shared UV2，`source/check_glb_assets.py`独立解析三份GLB：八张颜色图逐像素保持，UV0与世界顶点组合对应旧v4，两端与动画共享同一UV2，确有LidOpen。

`source/bake_p12_irradiance.py`从序列化GLB矩阵／顶点直接构建world-space烘焙副本；合并前后核对精确顶点包络，避免导入层级／父级变换让盖体或接收网格换位置。`source/denoise_and_pack.py`用项目既有Blender原生流程降噪线性HDR，打包最终两图进独立母版；不平滑像素颜色图。`source/check_packed_source.py`重开验证实际网格、两UV、源PNG、最终HDR哈希与动画帧。

Godot导入后运行`runtime_check.gd`作真实动画／物理／实例隔离验证；`capture.gd`在实际房间保存审图截图。源RGBA图、分层Aseprite和参考来源仍保留在v4实验。本轮不重新生成像素图，无新增AI或PixelLab调用。

尚待后续：20舱推广与编号／状态／旧化差分，以及全室光照统一。本轮单舱外部编号12仍为P12样本，不应复制成20个相同编号。
