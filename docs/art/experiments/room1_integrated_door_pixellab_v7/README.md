# Room 1 主门 PixelLab 贴图 v7：审图候选

本轮针对 v6 门面像素贴图出现的大块多边形。**v6 的新旧化确实由手工 Python 图层绘制，没有调用 PixelLab**；其粗色块与上沿的 1–3 px 像素簇尺度不一致。本版按 [像素贴图工作流](../../PIXEL_TEXTURE_WORKFLOW.md) 使用 PixelLab 官方 `/inpaint-v3` 接口重新生成细节。门的模型、UV、尺寸、灯语、开闭、碰撞和 Room 1 灯光不变。当前只提供独立候选，不替换正式场景。

**顶部追加修正：**用户指出上一版保留的墙面上沿与 PixelLab 侧面／底部风格不统一。本次通过同一 PixelLab 接口单独重做顶部（[提示词](source/prompt_header.txt)、[输入](source/header_guide.png)、[遮罩](source/header_mask.png)、[原始输出](raw/pixellab_inpaint_v3_header.png)），新增 **10 generations**，只提交一次。移除整条厚沉积，改为与其他部位一致的零散细簇。最终 Aseprite 新增第三层 `pixellab_top_style_match`。当前累计三次调用、30 generations；本次用量见 [记录](result_header.json)。

本次 2,315 个改变像素全部位于顶部遮罩内，其他部位逐像素不变；母版回读与运行 PNG 一致，见 [检查](header_validation.json)。Godot 五状态截图已更新。当前顶部已不再使用旧墙面沉积层的可见像素；下文保留最初两次生成及组装来源记录。

[同机位与原生像素对比](preview.html) · [Godot 审图场景](../../../../scenes/dev/room1_integrated_door_pixellab_v7.tscn) · [可编辑 Aseprite 母版](editable/door_front_v7.aseprite)

## 来源与生成

输入仅包含本项目自身的门面导图和遮罩：[导图](source/guide.png)保留 r6 后墙矿物底色、认可的上沿细簇与原状态窗；[黑白遮罩](source/mask.png)指定 PixelLab 可返修的门面部位。**没有向 PixelLab 上传 Pixel Canals 的截图、模型或贴图。**实际提交的两版提示词分别在 [首次](source/prompt.txt)、[修订](source/prompt_revision.txt)。

| 结果 | 原始输出 | 实际 PixelLab 用量 | 取舍 |
| --- | --- | --- | --- |
| 首次 | [raw 1](raw/pixellab_inpaint_v3.png) | 10 generations | 边缘只有孤立点，在游戏镜头太弱；保留作对照 |
| 修订 | [raw 2](raw/pixellab_inpaint_v3_revision.png) | 10 generations | 采用：边缘形成更连贯的小像素簇，中心留白 |

安全任务记录为 [首次](result.json)和[修订](result_revision.json)；POST 各只执行一次，没有自动重试。使用本机已连接的官方 Aseprite PixelLab 账号读取凭证，仅在进程内发送给官方 API；密钥、账号信息和完整服务响应不写入仓库。两张原始 PNG 均原样保留。

## 结构配准与验收

PixelLab 修订图把状态窗周围的结构也重新渲染了一些。[组装脚本](source/assemble_texture.py)通过遮罩锁定原小窗、上沿细簇与外侧密封边，只让 PixelLab 原图的材质像素进入新图；**脚本没有绘制新的做旧细节**。[可编辑母版](editable/door_front_v7.aseprite)分为已批准导图和 PixelLab 材质两层。运行时 [PNG](../../../../assets/art/room1_integrated_door_pixellab_v7/door_front.png) 与 Aseprite 回读逐像素一致，112×184。

Godot 4.6.2 Compatibility 模式在原房间灯光、1280×720 相机下拍了关闭、认证黄灯、绿灯开启中、绿灯已开启、拒绝红窗五张图。与 v6 相比，门面不再有手工粗多边形；像素细节集中在边缘和封条，门中央保持平净。原灯语和运动沿用 v6，未在本版重新定义权限或安全规则。这个检查不代表用户已认可美术效果。

复现顺序：运行 `source/prepare_input.py` 重建原创导图和 API 遮罩；既有原始 PixelLab 输出已保存在 `raw/`，**不要重复 submit**；运行 `source/assemble_texture.py` 组合，经 `source/package_layers.lua` 用 Aseprite 导出，Godot 导入 PNG 后运行 `scenes/dev/room1_integrated_door_pixellab_v7_capture.tscn`。`source/request_pixellab.py` 只用于查已提交任务或明确需要新生成时发送新请求，不能用重跑来复现既有像素。

## 与墙面的关系

现行 Room 1 墙面有 PixelLab 早期素材来源，但其 r3 接缝、r4 旧化、r5 全墙、r6 接缝修正为脚本／人工像素层，不能说它已完整符合本次新工作流。详见 [来源标注](../../PIXEL_TEXTURE_WORKFLOW.md#现有-room-1-墙面的来源标注)。本轮未擅自重做现行四墙。
