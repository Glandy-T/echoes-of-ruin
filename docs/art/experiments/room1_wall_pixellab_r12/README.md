# Room 1 墙面 PixelLab 差分 r12

2026-10-29。用户认可r11去除旧做旧后的墙面方向，要求增加差分，避免每面墙出现相同痕迹。本轮保持已认可的颗粒、配色、材质和结构，新增PixelLab原始差分e／f／g／h，再将a–h的8张原生图按既有接缝拆为**16种单墙板**安排到整室。

其中首张e在墙脚产生粗剥落块，已弃用，改用PixelLab重做的e2；墙板ID e0／e1均来自e2原图，不使用被弃用的e。

[游戏与四墙对比](preview.html) · [Godot场景](../../../../scenes/dev/room1_wall_pixellab_r12.tscn) · [四份Aseprite](editable/)

## 分配规则

同一面墙的墙板ID不重复；相邻墙板不使用同一原图的两个半幅，相对墙面同序号也不使用同一墙板，四角两侧错开同类痕迹。安排固定保存于 [assembly.json](source/assembly.json)，不在游戏运行时随机。**没有镜像、拉伸或旋转纹理来冒充新差分。**材料输入仍是r11的干净结构；旧手工做旧层仍不参与合成。

墙板按128像素的原有接缝模数精确裁分，密封芯和灯罩位置统一，原生像素密度不变。后墙门所在宽墙板继续使用已审过的r11 portal2，避免更改刚确认的门头与门面效果。

## PixelLab与源文件

新增e／f／g／h／e2五次官方 `/inpaint-v3` 调用，每次10 generations，本轮 **50 generations**（含弃用的e）。旧a／b／c／d及portal2只复用r11保存的原图，没有再次计费。新原图在 `raw/`，实际用量为 `result_*.json`；任务、固定seed、原创guide／mask、提示词和每张差分的附加描述在 `source/job.py` 与 `source/`。不上传Pixel Canals作品图像或账号凭证。

`source/assemble.py`只裁切原图、固定分配与结构遮罩，不绘制脏污。每份Aseprite仍只有干净结构＋PixelLab材质两层，运行PNG与母版回读逐像素一致。四个干净底图、灯带、门头、房间／模型／UV／灯光与r11相同，未重烘焙间接反射。

## 验证与审查

`source/quality.json`核对16种墙板的实际像素哈希均不同、每墙安排无ID重复、相邻同类错开、门所在墙板与r11逐像素保持、灯罩和转角边界精确保持、Aseprite读回一致及N诊断往返画面一致。Godot实际截图覆盖左／中／右游戏镜头、技术近景、四角与显示实体的前墙。图像仅证明交付范围与本轮巡检，视觉是否更自然仍交用户审图。

新场景默认r12；B／V／M对比r11和r12，N颜色诊断，J回观察点。正式游戏入口尚未替换。复现使用已保存原图，不要再次submit；依次运行 `source/assemble.py`、Aseprite `source/package.lua`、Godot捕获场景及 `source/review.py`。
