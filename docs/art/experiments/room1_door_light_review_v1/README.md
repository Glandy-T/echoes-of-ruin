# Room 1 门灯审图 v1（在 r32 门上重拍）

2026-11-17。门面 r32 已确认，按清单 1b 审门灯。**本轮没有改动任何灯光、颜色、亮度或节奏**，只是把 10/29 交付后一直未确认的 r17 内侧灯芯和 r18 柔光，放到 r32 门上重新同机位截图。

- [审图页](preview.html)：先看五个状态的近景拼图，再看通行状态 r17／r18 的游戏镜头放大图。
- 截图驱动：`scripts/dev/capture_room1_door_light_review_v1.gd`（场景 `scenes/dev/room1_door_light_review_v1_capture.tscn`，继承 r32 场景，门面为 C）。
- 互动查看：F6 `scenes/dev/room1_door_powder_r32.tscn`，按 3 切到 r32，F4 切换 r17／r18。

## 现有灯语（来自 v3 门脚本，未修改）

| 状态 | 小窗 | 门框内侧灯 |
|---|---|---|
| 待机 | 近黑 | 灭 |
| 认证中 | 黄色闪烁，0.5 秒一周期，其中 0.30 秒亮 | 灭 |
| 拒绝 | 红色常亮 | 灭 |
| 通行 | 绿色 | 内侧一圈绿灯；r17 为细硬灯芯，r18 为灯芯加两层屏幕空间柔光 |

## 截图中看到、需要用户判断的地方

1. **r17 还是 r18**：r18 的线条更粗、更亮，带有薄光晕；r17 是细而干净的灯芯。
2. **小窗发光区没有填满凹口**：黄、红状态下，亮色只占凹口上部约三分之二，下面留一条暗边。这条暗边是故意设计的，还是发光块和 r30 凹口没对齐，需要确认。
3. **门框竖向灯条在上下两端有轻微斜折**：游戏镜头放大图里，左右竖灯在接近上下两端时向内斜了一小段。r17 和 r18 都有，看起来像灯槽的透视或建模接缝。

以上只是记录，没有修改。

## 复现

1. Godot 4.6.2：`Godot --path . --resolution 1280x720 scenes/dev/room1_door_light_review_v1_capture.tscn`。
2. `python docs/art/experiments/room1_door_light_review_v1/source/build_review.py`（Pillow）。
