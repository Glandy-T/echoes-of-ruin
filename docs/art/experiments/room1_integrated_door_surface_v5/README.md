# Room 1 主门旧化分布 v5 · 审图候选

本版从 [v3 门](../room1_integrated_door_v3/README.md) 继续，修正其底部集中的旧化方式。[v4 提亮尝试](../room1_integrated_door_v4/README.md) 已退回；本版完全沿用 v3 的门面 Shader、亮度、门体尺寸、侧滑、碰撞、状态窗和授权绿灯，只替换门面像素图。正式游戏场景尚未切换。

## 做法与依据

v3 直接裁用了后墙的下段贴图，连墙脚积灰轮廓一起带到了会移动的门叶上，随后又在两侧下缘叠加了旧接触痕。那是配色复用的捷径，不是这扇门的实物老化证据。

本版保留同一组 r6 墙面矿物色阶与 80 texel/m 的颗粒，却不复制固定墙脚的大片沉积。旧化限制在滑动密封边的局部接触区、状态窗的凹边与底部两像素宽的接触带；主体表面由原墙的低对比大面材料色差维持，不画无来源的漏液、手印或散布污斑。现实气密滑门的密封件、门框和贴地封条是合理的接触位置；这只能支持痕迹**放在哪里**，不能证明 80–100 年后它们一定呈现本贴图的具体形状和浓度。参考：[Dortek 的气密滑门结构与密封件磨损说明](https://dortek.com/wp-content/uploads/2021/03/Dortek-Hermetic-doors-for-cleanrooms-and-operating-theatres-technical-article.pdf)、[室内颗粒在水平面与竖直面沉积差异的研究](https://www.nature.com/articles/BMC2050-7445-1-7)。时间尺度来自项目 [WORLD_BIBLE](../../../WORLD_BIBLE.md)。

门底在 Godot 截图里仍偏暗，有一部分来自 v3 的应急照明明暗 Shader，而非贴图污渍。v5 不加入任何真实灯，也不使用 v4 的底部补亮项。

## 交付与验证

- [同镜头 v3/v5 对比及贴图放大查看](preview.html)，Godot 实拍 1280 × 720。
- [Aseprite 三图层源](editable/door_front_v5.aseprite)、[图层生成脚本](source/build_pixel_layers.py)、[Godot 使用 PNG](../../../../assets/art/room1_integrated_door_surface_v5/door_front.png)。Aseprite 回读与运行 PNG 逐像素相同，112 × 184 像素。
- [Godot v5 审图场景](../../../../scenes/dev/room1_integrated_door_surface_v5.tscn)只把门面的 `pixel_map` 指向新 PNG；v3 GLB 和原有场景继续可用。另有 [截图场景](../../../../scenes/dev/room1_integrated_door_surface_v5_capture.tscn)。
- 这轮验证了 Godot 重新导入与关门／认证／开门五状态截图；门的位置、运动和碰撞继承已验证的 v3，不把截图当作新的运动验收。

此版是旧化逻辑候选。具体可见度与全室统一感以游戏镜头审图为准。
