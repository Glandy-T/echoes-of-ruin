# 主角正面 v2：弱化五官与肤色

2026-11-03。状态：**待审正面候选**。用户确认沿《INSIDE》式弱化五官方向修正v1的沉重神情，并把肤色提浅；此处借鉴面部信息简化方法，不复制角色，也不上传参考截图。白袍、头发、身体比例、姿势与透明轮廓保持v1。

- [同尺寸全身与面部局部对比](preview.html)
- [最终PNG](front_design_v2.png)：192×256原生，无缩放。
- [Aseprite母版](editable/front_design_v2.aseprite)：v1原层＋PixelLab肤色／面部修改层＋有名称的局部美术精修层。
- [当前主角简报](../../PROTAGONIST_LOW_POLY_BRIEF.md)；[v1来源](../protagonist_front_v1/README.md)。

## 实际制作与来源

一次官方`POST /v2/inpaint-v3`，任务`0861a33f-07d0-4c24-8811-3f0085394dfc`，实际**10 generations**。`source/requests.json`、`prompt_front.txt`、`input_front_v1.png`、`skin_face_mask.png`保留原创输入与实际请求；`raw/front.png`为未修改PixelLab原始输出，`result_front.json`保留用量。没有额外抽图，没有上传Pixel Canals／INSIDE或其他第三方图片。

PixelLab负责脸、颈、手和脚的浅肤色与面部色块。保护遮罩来自v1的五个原生肤色，并填入脸部旧五官之间的内孔，用于限制生成范围。`compose.py`只做原生遮罩配准，不绘画，不缩放。

实际查看AI结果后，仍能看到眉线、眼白／眼点和嘴部标记，且旧保护边界保留了五个眉部深色像素。因此按已授权Aseprite局部精修流程，在`Aseprite_remove_remaining_brows_eyes_mouth_keep_simple_nose_plane`独立层清理残留五官：沿用AI已有肤色，清理眉眼与嘴线，减轻下巴线，保留两像素的低对比鼻侧面。**在已配准AI结果上实际精修54像素**，不是“未经修改的PixelLab成品”；`source/package.lua`保留明确局部操作。

最终相对v1共改变1427个可见像素。范围只涉及肤色／脸部信息；衣服、头发外轮廓与其他像素保持。Aseprite在全透明区可能写白色RGB，`finalize.py`仅将alpha=0下不可见RGB恢复为输入值，便于逐字节范围校验，没有改动可见美术。

## 检查与观察边界

`source/validation.json`核对192×256、v1源哈希不变、透明轮廓不变、范围外像素精确一致、最终图与Aseprite所有可见像素一致及实际任务用量。`source/composition.json`记录精修前AI配准阶段；最终检查以`validation.json`为准。

实际查看了原生全身和同区域头部裁片：肤色比v1更浅，深色眉眼与嘴角已去掉，仍保留简单的面部朝向和体积；服装与长发保持原造型。是否喜欢这种简化程度仍由用户审图决定，不把技术检查当成视觉批准。

面部裁片仅用于预览，没有用来生成或改变素材密度。尚未制作侧背面、3D、绑定、UV或动作，也没有替换Godot临时主角或改动Room 1。后续三视图与3D参考采用认可后的v2方向，不能回用v1细画五官作为建模细节。

复现顺序：保留已有任务／raw，不重复付费POST；`compose.py` → Aseprite批处理`package.lua`（参数`root`）→ `finalize.py` → `build_preview.py`。
