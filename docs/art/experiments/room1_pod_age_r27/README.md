# Room 1 单舱颗粒与做旧 r27

2026-11-02。状态：**P12代表舱已制作，等待用户审图；未推广其他19舱，未替换正式F5。**

按[新制作基准](../../PIXEL_ART_PRODUCTION_STANDARD.md)执行：Pixel Canals作为实际颗粒、像素簇和表面完成度参考；PixelLab主体制作，Aseprite允许局部精修。本轮只提交本项目原创结构导图，没有向AI上传参考作品的NoAI内容。

## 查看与范围

- [同机位A/B对比](preview.html)：原r26／新r27，闭合、开盖、整舱、长侧、短端与内侧；另存两张basecolor诊断，共17张真实1280×720 GPU截图。
- F6：`scenes/dev/room1_pod_age_r27.tscn`；1原r26、2本轮P12材质、O开闭、H说明。正式F5仍是r19，完整美术候选仍保留r26。
- Blender：`room1_pod_age_r27.blend`，从r26另存完整房间，仅P12三个外壳材质绑定改图；相对依赖同一仓库，不能只拿走blend而不带贴图。
- 三个运行PNG：`assets/art/room1_pod_age_r27/{lid,shell_side,shell_end}.png`。
- 三份可编辑Aseprite：`editable/`；PixelLab原始输出：`raw/`。

只改P12盖板、长侧壳、端壳的`color_map`。模型、UV、房间布局、其他19舱、墙地、灯光、玻璃、动态屏幕、编号12、双侧灯管和开闭方案保持；没有换Shader或重烘GI。贴图变化后的间接反弹尚未重算，本轮用于隔离审查材质。

## 原生密度与来源

最终盖板96×184、侧壳184×56、端壳96×56，均为实际PixelLab原生输出尺寸。原始输出没有缩小、放大或模糊；只有原创结构导图和功能编号做UV配准，旧做旧层没有叠入新可见材质。

`source/measure_density.py`读取实际GLB三角顶点与UV的雅可比：主要盖面约80／83.48纹素每米、长侧主面约77.91／80、端面主面约77.91／83.48。不是用“整张图÷包围盒”推断。既有斜肩、窄条和小倒角的UV密度仍有差异，报告保留全分布，**不宣称所有表面都已严格80**；本轮不改UV以免改变已确认模型。

实际调用官方`POST /v2/inpaint-v3`及后台任务查询。共**4次成功请求、40 generations**，最终使用3张输出；任务ID与真实用量在`result_*.json`。第一张盖板96×256被拒用：逐面测量发现其长轴仍为111纹素／米，随后由PixelLab重新生成96×184；没有通过缩小该输出修正。拒用图、初始导图／遮罩、任务记录与原因保留在`raw/lid.png`和`source/initial_density_attempt/`、`rejected_outputs.json`。这是一项有测量依据的尺寸修正，不是另开风格试验。

新做旧以密封边、肩部、凹槽、端角与下沿的成组沉积、局部涂层变化为主，主面保留浅色差与细碎材料变化。正常照明下比r22旧壳更可读，仍保留完整、标准化设施的感觉，不做锈黄色、破洞或恐怖破损。

Aseprite母版分为原创结构、PixelLab新材质、功能编号和独立局部精修层。这轮AI结果没有需要再造型的局部缺陷，**精修层保留为空，实际美术手绘改动0**，只作结构／编号配准和分层整理；不为了使用精修工具而制造额外改动，也不把它称为已经手绘精修。后续明确局部反馈可直接在该层处理。

## 检查与复现

- `source/artifact_validation.json`：20项文件检查，Aseprite回读与运行PNG逐像素相同，编号／结构保护和原生尺寸验证。
- `source/runtime_validation.json`：28项运行检查，A/B只换P12三张颜色图，包含运行时Texture2D实际尺寸与解码像素检查；其他19舱、UV、屏幕、玻璃、灯与受保护状态保持。
- `evidence/capture_record.json`及`source/capture_validation.json`：17张最终截图；A→B有实际差异，闭合A→恢复逐像素相同。捕获使用完整路径、OpenGL3，每帧记录实际加载图的尺寸／解码哈希。曾发现lid导入缓存仍旧，已完整重新导入并核对三图source/import MD5一致后重拍全部17帧；旧记录不当作最终验收。
- `source/blender_readback.json`：131对象的几何／UV／变换／灯／相机保持，只有P12三处材质换图；253张外部图无缺失、无绝对路径。
- `source/baseline_hashes.json`：17份既有工程、模型、墙地、GI及原贴图未变。
- `source/independent_review.json`：独立检查通过，复核原始输出／Aseprite／Blender与最终运行图，并记录已解决的导入缓存问题；不替代用户最终美术认可。

复现不需新生成：用已有raw运行`source/compose.py`，Aseprite批处理运行`source/package.lua`（参数`root`为本实验绝对路径），再运行`check_artifacts.py`。`prepare.py`只重建原创输入；不要为重新打包再次付费请求。Blender源由`source/blender_material_source.py`从r26另存。Godot验证／捕获入口为同名`*_verify.tscn`／`*_capture.tscn`，GPU捕获参数使用`--rendering-driver opengl3`。

技术通过不替代用户对做旧强度和颗粒的最终认可。代表舱确认后才推广差分；不在本轮自由重做全室或开始主角建模。
