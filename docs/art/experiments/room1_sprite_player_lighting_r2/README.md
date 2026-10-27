# Room 1 纸片主角受光 r2

入口是 `scenes/dev/room1_sprite_player_lighting_r2.tscn`。它保留 r1 的原始 idle/walk PNG、1.65m身高、角色碰撞、移动、镜头朝向和纸片遮挡，只为可见 Sprite3D 加入受灯带控制的低亮度受光近似。

房间墙地使用静态烘焙光图，动态的面向镜头精灵无法直接接收那张图。本轮 shader 使用同一条连续灯带的八组位置，按角色到各段的距离计算冷白低功耗照度。L关闭灯带时角色仅留极弱环境可读性，打开时随位置变亮；它不是动态GI、阴影投射或新的全局光照方案。

`evidence/` 包含同机位开灯、关灯、恢复和行走截图。`capture.gd` 实际运行场景并检查 walk 帧与移动距离；`check_capture.py` 检查角色所在画面区域在开灯／恢复时确实比关灯亮，结果写入 `capture_quality.json`。旧 r1 保留，正式入口未替换。
