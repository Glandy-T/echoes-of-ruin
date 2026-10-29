# Room 1 四墙 PixelLab r11 — 清除旧做旧后统一重做

> 用户已认可本版方向，并要求增加差分；后续安排见 [r12 更多墙板差分](../room1_wall_pixellab_r12/README.md)。r11继续作为材质风格基准。

2026-10-29。用户认可r10的像素细化方向，但指出新图仍混着旧的粗做旧。本版从**无旧化的干净建筑结构**开始，由PixelLab重新生成整套四墙表面；当前审图场景默认全部显示r11，B切旧r6只用于历史比较。正式游戏入口暂未替换。

[完整对比](preview.html) · [Godot场景](../../../../scenes/dev/room1_wall_pixellab_r11.tscn) · [四墙Aseprite](editable/)

## 清除的旧内容

新底图只合成原工程的 `base`、`structure`、`joints`：底色、灯槽／灯罩、连续金属保护带和既有接缝。**没有合入** `quiet_mineral_plane`、`top_deposit`、`lower_accumulation`、`joint_seal_film`、`base_contact`。因此原大块面层色差、粗阶梯沉积、矩形缝边旧膜和保护带旧接触都已从新底图删除。

每份新母版只有“干净结构”和“PixelLab新材质”两层。不存在旧成品墙图＋AI细碎像素的叠加。生成图按技术遮罩配准到结构上，脚本没有补绘新的脏污；旧r6纹理仅在B键历史对照模式中装载。

## PixelLab生成与差分

用项目自有256×256干净导图生成a／b／c／d四种差分，材质细节覆盖上沿、缝肩、墙脚和金属保护带的接触面。门所在的宽墙板另做无中央接缝的portal2差分，避免复活门头旧缝。像素密度沿用80 texel/m；左右墙728×272、前后墙1648×272。差分按固定序列安排在原接缝模数内，不在运行时随机变化；放置见 [assembly.json](source/assembly.json)。四面墙都已替换。

全部细节生成／返修使用官方PixelLab `/inpaint-v3`。六次提交各10 generations，共 **60 generations**：a／b／c／d及portal2采用；首张portal出现额外横缝和剥落，已明确弃用，原图保留但不进入组装脚本。任务、固定seed、prompt、导图／mask、原始PNG和实际用量均保存在 `source/`、`raw/`、`result_*.json`；POST不自动重试。没有向AI上传Pixel Canals作品图像。

## 结构与导入

灯罩像素和连续结构高度精确保持；仅密封芯及真实墙角两列受保护，缝肩允许新材质接触，不挖旧化隔离空边。门头保留当前无中央竖缝的施工结构；门叶、绿灯、小窗、开闭、20舱、人物位置、地面、碰撞、布局与模型均沿用当前版本。

`source/prepare.py`只提取干净结构，`source/assemble.py`只对位遮罩与放置差分，`source/package.lua`用Aseprite打包四份母版并独立回读。运行时PNG在 `assets/art/room1_wall_pixellab_r11/`。已保存raw可直接复现，不要重复submit。

## 验证与审图边界

`source/quality.json`核对新底图确实只来自上述三个结构层、四份母版／PNG逐像素一致、灯罩与转角边列不变，以及N颜色诊断恢复后的画面一致。Godot捕获脚本还核实所有墙面接收材质实际绑定四张r11图，不继续混用r6或旧门洞颜色图。

Godot 4.6.2 Compatibility在原光照下捕获左／中／右游戏镜头修前后、材料近景与Base Color、四个真实转角和显示实体的前墙。巡检相机只用于截图，不保存进游戏镜头。新固有色反射未重烘焙；本版是完整四墙的材质候选，不宣称是新全室光照包。表面风格与旧化强度仍待用户审图。
