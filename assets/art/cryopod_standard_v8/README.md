# Cryopod Standard v8

`cryopod_standard_v8.glb`含真实LidOpen动作、固定壳及玻璃／内腔／灯管实体。closed/open两份GLB是同源静态端点，用于核对／烘焙，运行时使用单个动画GLB。

Godot可复用入口：`scenes/props/cryopod_standard_v8.tscn`。房间验收入口：`scenes/dev/room1_pod_standard_v8_review.tscn`。不要将原v3/v4静态舱叠放到该实例上。

UV0为原像素颜色，UV2为一次共用布局；closed/open HDR按同一UV2采样，属于P12位置受光，不是任意舱位通用光照。玻璃、灯管和屏幕需附带Godot材质／控制器，裸GLB预览不包含全部运行时效果。

可编辑Blender、像素母版来源、动画／碰撞／接口与验证限制见 `docs/art/experiments/room1_pod_standard_v8/README.md`。独立母版包含八张原像素图与最终P12 HDR，无外部图像缺失依赖。
