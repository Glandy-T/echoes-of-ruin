# Room 1 墙面 PixelLab 返修 r10 — 局部审图

> **已由 [r11 四墙新材质](../room1_wall_pixellab_r11/README.md) 接替。**用户认可细化方向，但指出r10输入和边界仍带有旧做旧。r11从无旧化的结构导图重新生成，不再沿用r10混合来源的母版。

2026-10-29。用户要求将旧贴图按已约定的 PixelLab 工作流返修。本轮先完成左墙中间两块墙板的材质细化小样，**等待审图，不替换正式场景或推广四墙**。以 Pixel Canals 的像素簇与材质信息组织为硬参考；只向 PixelLab 提交本项目自有图像。

[同机位对比](preview.html) · [Aseprite 母版](editable/wall_left_r10.aseprite) · [Godot 场景](../../../../scenes/dev/room1_wall_pixellab_r10.tscn)

## 范围与结果

当前左墙 r6 的缝边有较大的矩形旧膜，上沿／墙脚有规则阶梯带。通过 PixelLab `/inpaint-v3` 将它们细化成依附结构、疏密变化的细像素簇，主墙面保留完整留白。保留原暖灰配色、连续蓝白灯带、接缝位置及密封芯、金属保护带、模型、UV、人物／舱位、相机和照明。

输入为 r6 左墙 x=128–384、y=16–272 的原生 **256×256** 裁片，约3.2m宽；[guide](source/guide.png)、[mask](source/mask.png)、[prompt](source/prompt.txt)、[PixelLab原图](raw/pixellab_wall.png)均留存。拼回728×272整墙时仅做结构遮罩与样段边缘四像素一阶的过渡，没有另画污斑。当前修图区位于 x=0.2m 的左墙，z=-5.0至-1.8m一带。B键比较r6／r10，J回观察点，N看颜色诊断。

首次384×272请求因“Tier 2 is required for this”失败，API返回费用0美元；原输入、任务与错误保存在 `source/failed_large/`。缩小后的请求成功，实际消耗 **10 generations**，见 [result](result.json)。无自动重复POST。账号凭证只由既有官方连接在内存中读取，未进入仓库。

## 可编辑与验证

Aseprite两层：原r6整墙＋PixelLab生成材质的遮罩层；运行时PNG以Aseprite实际导出为准。`source/assemble.py`只对位与遮罩，`source/package.lua`打包母版，`source/review.py`检查范围并生成本对比页。源与最终PNG逐像素一致。

[quality.json](source/quality.json)记录11,547个改变像素，全部落在指定遮罩内；灯罩、真实墙角边列及两个密封芯不变。Godot 4.6.2 Compatibility实际导出11张1280×720截图：游戏镜头、近景、Base Color修前／后，N恢复图及四角巡检。技术巡检临时显示被剖切的前墙，结束恢复。实际看过巡检，未发现这次新增的光照裂缝或样段矩形接头；周围旧墙面的粗块仍明显可见，属于之后推广返修的对象。

本轮没有改模型、UV2或烘焙数据，沿用既有配套光照。新颜色引起的间接反射尚未重烘焙，这是一份材质审图样段；未把它声明为新全室烘焙包或已通过美术验收。

## 后续次序

1. 先审本样段的颗粒、旧化密度和暗光可读性；认可后，以PixelLab制作四面墙的差分，连续灯槽、转角与缝芯按技术边界统一。
2. 再返修地板旧流程的材料和接触痕迹：保持连续统一蓝灰地坪，不加砖缝、路线或黄色污迹。
3. 已认可的门面／休眠舱继续作为当前基线，发现具体风格或设计问题时再定点返修。
