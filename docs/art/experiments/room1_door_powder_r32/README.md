# Room 1 门 r32：M05-L 粉末涂层钢板

2026-11-17。用户确认 **Room 1 主门材质定为 M05-L 粉末涂层钢板**（与建筑执行包中 FD/EN 门同一家族）。r32 按此改贴图，**待审，正式 F5 未切换**。

- [三方对比页](preview.html)：A＝r30，B＝r31，C＝r32，同机位 1280×720。先看最上面的游戏镜头门区和近景。
- F6：`scenes/dev/room1_door_powder_r32.tscn`，按 **1／2／3** 切换 A／B／C。
- 运行贴图：`assets/art/room1_door_powder_r32/door_front.png`（112×184，80 px/m，与 r30 同尺寸同 UV）。
- 分层母版：[editable/door_front_r32.aseprite](editable/door_front_r32.aseprite)，三层：
  1. `01_M05-L_powder_coat_native_crop`：M05-L 原生裁片 (12,52) 112×184，无缩放、无翻转；
  2. `02_r30_darker_traces_on_new_base`：r30 中比涂层暗的痕迹，按原有的相对深浅迁到新底材上（新值＝底材×r30/r30涂层色）；
  3. `03_r30_seal_ring_and_status_aperture`：r30 的 1px 密封边与小窗，原值保留。
- **没有新生成**：所有像素都来自 M05-L（PixelLab 原生）和 r30（r29 PixelLab＋r30 Aseprite 精修），PixelLab 消耗 0。来源哈希与像素统计见 `source/layer_record.json`。

## 改了什么、为什么

1. **底材换成 M05-L 粉末涂层**：r30 主面 80% 是同一个颜色，M05-L 整面都有均匀的细粉末颗粒。
2. **不带 r30 的亮像素**：r30 共 984 个比涂层亮的像素，其中 74% 在门边 4px 内，连起来就是一圈亮边。M05 规格写明"不能画亮色整圈磨边"，这圈亮边也正是读成不锈钢包边的原因，所以没有迁过来。
3. **着色器沿用 r31，参数针对 r32 重新校准**：亮度按墙面逐段对齐。颗粒分成两部分处理（当前为第二次修订的中间值）：M05-L 的细粉末颗粒 **1.25 倍**，r30 的痕迹、密封边和小窗 **1.5 倍**。分界按像素偏离中位色的程度划定（亮度差 0.04～0.09 之间渐变）。参数见 `scripts/dev/room1_door_powder_r32.gd` 的 `R32_PARAMS`，着色器新增的 `fine_contrast` 默认关闭，不影响 r31。

### 修订记录（同日）

第一版 r32（[`9fe87dd`](https://github.com/Glandy-T/echoes-of-ruin/tree/9fe87dd/docs/art/experiments/room1_door_powder_r32)）把所有颗粒放大 2 倍，用户指出**门比墙更显痕迹**。原因是当时把门和"整块墙"做比较：墙的颗粒集中在板边和墙角的沉积里，板面中间其实很安静；门却是整面均匀铺满颗粒。改为只比较"门板中间"和"墙板中间"后，第一版门面的可见颗粒像素是 13.0%（墙板 3.2%），安静区域只有 29%（墙板 78%）。

修订时还试过把所有颗粒统一压到 0.8 倍。这样数字接近墙板，但小窗凹口和暗痕迹也会一起变淡，所以改成只压细粉末颗粒。第一次修订（[`381ae80`](https://github.com/Glandy-T/echoes-of-ruin/tree/381ae80/docs/art/experiments/room1_door_powder_r32)）把细颗粒压到 0.5 倍、痕迹保持原样，用户认为又偏淡，要求**在第一版和第一次修订之间取中间值**：细颗粒 1.25 倍、痕迹 1.5 倍。

## 测量（`source/measurements.json`）

| 项目 | A r30 | B r31 | C r32（第二次修订，中间值） | 墙面 |
|---|---|---|---|---|
| 游戏镜头门区六段亮度（绿通道，上→下） | 36 → 18 | 38 → 27 | 38 → 28 | 39 → 28 |
| 正面镜头平均亮度 | 27.3 | 33.6 | 33.8 | 33.4 |
| 板面中间：可见颗粒像素 | 3.9% | 4.6% | 8.3%（第一版 13.0%，第一次修订 4.5%） | 3.2% |
| 板面中间：安静区块 | 85% | 81% | 48%（第一版 29%，第一次修订 75%） | 78% |

当前 C 的颗粒量在第一版和第一次修订的正中间：比墙板中间明显，但不再像第一版那样整面铺满。这是用户选择的取舍，不追求和墙板数字相同。痕迹仍按 M05 规格只在边缘和小窗附近成小簇。

## 校准中发现的问题（同时更正 r31）

本项目用 `gl_compatibility` 渲染器，着色器里读到的 `pixel_map` 是 **sRGB 编码值**，不是线性值。证据：参考值用 sRGB 中位色时，颗粒强度从 1 调到 5，门的平均亮度几乎不变；用线性中位色时，亮度会随强度明显上升。r32 的 `grain_reference` 用 sRGB 中位色 `(0.631, 0.667, 0.635)`。

r31 的参考值当时按线性空间计算，落在 r30 涂层色之下，所以 r31 实际只做了约 1.2 倍的整体对比放大，并没有像说明里写的那样"暗痕迹 ×2.6"。r31 截图和测量数据都是真实渲染结果，只是原因描述有误；r31 说明已加更正，r31 参数保持不变，以便原样复现。

## 验证

`evidence/capture_record.json`：

- A→B→C 后切回 A、B，画面与第一次逐字节一致；
- r32 场景里的 A、B 与 r31 交付的 A、B 截图哈希相同；
- C 的认证黄窗、开启绿灯、门开和柔光状态图已检查（只换了贴图和着色器参数）；
- Aseprite 导出图与 Python 合成预期逐像素一致（0 像素差异）。

门形、UV、动画、认证逻辑、门框灯、房间光照、烘焙都没有改动。4F 走廊仍使用 v3 门着色器和 r30 贴图；如果 r32 被采用，还需要同步到 4F 走廊与正式 F5。

## 复现

1. `python docs/art/experiments/room1_door_powder_r32/source/build_layers.py`（Python 3.11＋Pillow＋NumPy）生成三层 PNG。
2. `aseprite -b --script-param root=<仓库根> --script docs/art/experiments/room1_door_powder_r32/source/build_aseprite.lua` 组装母版并导出运行贴图。
3. Godot 4.6.2：`Godot --path . --resolution 1280x720 scenes/dev/room1_door_powder_r32_capture.tscn`。
4. `python docs/art/experiments/room1_door_powder_r32/source/build_review.py` 生成对比图、测量和审图页。
