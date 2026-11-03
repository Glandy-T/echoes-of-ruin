# 主角正面造型 v1

2026-11-03。状态：**一张待审设计稿**，没有侧面／背面／3D模型，不替换Room 1角色占位。详见[当前主角制作简报](../../PROTAGONIST_LOW_POLY_BRIEF.md)。

用户本轮确认服装大方向为简单白袍、有统一休眠服的感觉，并提出时间痕迹。第一稿沿用深色长发与年轻女性印象，采用自然成人比例、平视全身正面、双臂稍张开。闭合圆领、长袖、约小腿下部袍长、赤足、具体发型均为待审解释，不把本稿当成最终设计。

## 看稿与源文件

- [原生与放大预览](preview.html)
- [PixelLab原图](raw/front.png)：192×256原生，透明背景，没有缩放或手绘改动。
- [Aseprite母版](editable/front_design_v1.aseprite)：`PixelLab_original_front_design_v1`原图层，另留`Aseprite_local_refinement_empty`空精修层。实际局部美术精修0。
- `source/request.json`／`prompt_front.txt`：实际提交正文；`generate.py`支持保存任务后继续轮询，不能重复POST。
- `result_front.json`：实际任务与用量；`source/validation.json`：尺寸、alpha、Aseprite回读及来源核对。

## 来源与用量

官方`POST https://api.pixellab.ai/v2/create-image-pro-flash`，**一次请求、一张成稿，实际9 generations**。任务ID`cbfee5a0-f73c-414b-a0d9-6ff2e6ac7deb`，保留`source_image_id`供可能的后续方向生成使用。原始请求为文本，没有上传Pixel Canals或其他第三方图像，没有上传旧角色试作。

本张画布是造型参考的试作尺寸，不等于未来角色贴图分辨率或游戏画面尺寸。服务端按其生成流程返回所请求的原生网格，本地没有缩小／放大后重绘。接口描述核对于2026-11-03的[官方文档](https://api.pixellab.ai/v2/docs)。

## 观察与待定

实际查看了正面原图：单个全身人物、头顶／手／脚完整；自然比例、正面轮廓与白袍可辨。白色布料以冷灰折痕和轻微色差表达保存时间，没有重污斑、大面积泛黄或破损；当前旧痕较轻，不宣称用户已认可强度。头发背后体积、服装侧后结构和衣服开合方式仍未定义，不从正面图擅自推定。

下一步是用户看这张正面是否接近想要的人，再针对具体轮廓／脸／发型／袍长收敛；认可后补同设计的侧面、背面并对齐比例。没有开始三视图批量生成、3D生成、UV、绑定或动画。Godot模型／镜头／灯光／占位角色均未改，也没有做“实机角色通过”的结论。
