# Room 1 — PixelLab 舱盖底图编辑试验 v1

2026-10-13。用户完成订阅后要求继续。本轮实际使用 Chrome 扩展连接 PixelLab Web Creator，从项目自制颜色底图生成舱盖贴图；另存单舱与全室 Blender 对照。原 v4.1 舱体、全室工程及上一轮墙／地面试验保留。

## 范围与状态

只替换休眠舱不透明舱盖外表面的基础颜色。没有改变网格、房间布局、20 个舱位、门、镜头、灯光或开盖动作；头部玻璃、床面、脚端屏幕和固定舱体保留原材质。

**状态：底图上传 → PixelLab 编辑 → 原始 PNG 保存 → Aseprite 可编辑文件 → Blender 试贴流程已实际执行；贴图仍待用户视觉审查。不是最终舱体母版，也没有在 Godot 内运行。**

## 实际生成

| 请求 | 模式／网页成本 | 结果 |
|---|---|---|
| 第一次 | Pro／10 | 保留主要颜色分区，但擅自添加接缝与螺钉状细节，不采用；保留 `lid_edit01_rejected.png` |
| 第二次 | Pro Flash BETA／9 | 使用同一底图，更明确要求抽象色块；未再出现第一张的接缝／螺钉，加入少量灰色像素簇；保存 `lid_edit02.png` 并试贴 |

账户页实际由 **0 / 2,000** 变为 **19 / 2,000**。128×256 的 Flash 编辑网页成本为9，不能套用上一轮64×64生成的5次成本。两次同时改变了提示词与模式，不能据此给模型排出普遍质量排名。本轮没有购买、升级或修改订阅。

上传最初被 Chrome 扩展的文件网址权限拦截。用户自行开启权限，扩展重连后，页面实际显示128×256输入底图。没有通过隐藏接口、密钥或权限绕过上传。账户读取仅定位套餐标题与“Generations”区域；没有记录账户凭据。

第二张下载在本机 Downloads 中保留为 `.tmp` 文件名；该文件可完整解码为128×256 RGBA PNG，本目录保存其原始字节副本，不覆盖或清理 Downloads 原文件。图像尺寸、颜色数、透明度与散列见 `source/image_inventory.json`。

## 颜色底图与 UV

- `source/lid_planar_color_GUIDE.png` 是128×256技术导引图：浅色中央大面、冷灰肩部色带、脚端灰色块。其分区为本轮试验，并未升格为项目色板。
- 这是单个不透明舱盖的平面颜色导引，**不是完整展开图，也没有向 AI 提交多个 UV 岛**。因此不能宣布 AI 已能精确保持复杂 UV 图集。
- 原有 `UV_PAINT_candidate` 保留。添加 `UV_LID_PLANAR_TRIAL_NOT_FINAL`，以网格本地XY坐标映射；开盖时贴图跟随舱盖移动。
- 图片通过 sRGB Base Color、`Closest` 采样接入原 Principled 材质。原审查照明、色彩管理和几何明暗沿用。
- 侧面与端面的投影密度不均匀；暂不作为最终绘图UV，后续需使用实际展开与统一 texel density。当前128×256本身不是项目标准。
- 第二张原始图为34种RGBA颜色，不满足提示中“六至八色”的严格约束。没有将生成图重新量化、重绘、去噪或放大后冒充原图。

## 观察与后续

1. 提供颜色底图后，AI能在本次两张输出中保留主要纵向色带与脚端色块；这比仅描述整件舱体更便于限制形状。
2. Pro仍会联想工业面板细节，即使提示禁止接缝和螺钉；需要实际审查，不能只信提示词。
3. 第二张的像素簇像几处简单斑点，功能与老化原因尚未确定；它只适合检查颜色与映射流程，不能直接认定为成熟像素绘制。
4. 固定舱壳、玻璃与屏幕仍是原灰模材质。当前画面仍有清楚的连续3D光照，尚未达到 Pixel Canals 参考的整体2D观感。
5. 下一轮先审查颜色大面与像素密度，再决定这些斑点是否保留。经确认后才推进固定舱壳表面、精确编号或屏幕内容；精确文字应另绘，不依赖AI随机生成。

## 文件与复现

- [对比预览](preview.html)：同镜头灰模／贴图，45°开盖与全室环境图。
- [单舱工程](room1_pixellab_pod_trial_v1.blend)、[全室对照工程](room1_context_pod_texture_trial_v1.blend)：试贴图已打包。
- [Aseprite 母版候选](textures/lid_pixel_master_trial_v1.aseprite)：原始AI图层与隐藏的技术导引图层；未通过 Aseprite PixelLab 插件生成。
- `apply_pod_texture.py`：以相邻v4.1单舱与上一轮贴图试验为来源，另存本目录工程。
- `source/prepare_guide.py`：生成技术底图；`source/build_editable.lua`：将AI原图与底图打包为可编辑图层。
- [生成记录](source/generation_record.json)、[图像清单](source/image_inventory.json)、`evidence/pixellab_edit*_result.jpg`：提示词、成本与实际网页证据。

使用 Blender 5.0.1 后台执行 `apply_pod_texture.py` 可重建工程与四张渲染图；`-- --guide-preview` 只输出技术导引图试贴。使用 Aseprite 的批处理 Lua 可重建可编辑候选。没有新增／运行自动测试、碰撞或游戏运行验证。

Aseprite 导出时已安装 PixelLab 插件报告 `handle-pose.lua` 的批处理对话框警告；等待批处理进程结束后，本次 `.aseprite` 文件实际保存成功。没有修改插件或应用配置，也不将此导出视为插件联网生成成功。

## 来源

两张候选由用户的 [PixelLab Web Creator](https://www.pixellab.ai/create) 账户生成。技术导引为项目自制；没有上传 Pixel Canals 的图像、贴图或模型。

舱体沿用 [v4.1 来源与修改说明](../room1_pod_reference_v4_1/README.md)：轮廓参考 Scifi - Cryogenic Sleep，作者 Artboard Silvio Pinheiro / scrpinheiro，用户提供 GLB 标记许可 CC BY 4.0；使用项目重建低模网格及头窗、整片舱盖、有限开盖与信息屏修改。全室与墙地材质沿用 [上一轮 PixelLab 试验](../room1_pixellab_texture_trial_v1/README.md)。
