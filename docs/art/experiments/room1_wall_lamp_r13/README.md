# Room 1 后墙补齐与灯带材质 r13

2026-10-29。用户指出门所在后墙显得没有更新，并建议灯带也补充细节。本版修正过疏的门洞宽墙板差分，同时用PixelLab制作连续灯带的灯罩／槽边材质；默认使用r13，B与r12比较。独立审图版本，正式游戏入口未替换。

[后墙与灯带对比](preview.html) · [Godot场景](../../../../scenes/dev/room1_wall_lamp_r13.tscn) · [四墙Aseprite母版](editable/)

## 后墙原因与修正

r12的后墙左右和门楣确实绑定了新图，但门所在x=688–944的宽墙板保留r11的稀疏portal2差分，视觉上比相邻墙板干净许多。不是其他三面墙用了新图而整面后墙漏绑定。本次在干净无中央竖缝的原生256×256导图上重新用PixelLab生成中等强度的边缘积灰，整块替换原portal2，保留门洞、门叶、小窗、绿框与通行机制。

Godot捕获脚本核实 `Wall_rear_left`、`Wall_rear_right`、`Wall_rear_door_header` 三个实际接收面的shader、surface kind、颜色图和间接光路径；当前均指向r13后墙图。记录在 [rear_bindings.json](evidence/rear_bindings.json)。新版本覆盖门洞贴图安装入口，避免后续又装回历史门洞图。

## 灯带材质与可见性

两张原生256×64PixelLab材质补充灯罩轻微浑浊、色阶和槽边积灰，不新增灯具、文字、断光、闪烁或死灯段。PixelLab原图擅自在画布边缘生成圆角灯具端头，因此只裁取每张中央128像素的连续材质，按结构遮罩与边缘技术过渡安排到四墙，原始图完整保留。脚本不手绘脏污或造新细节。

旧shader把发光面推到显示白色以上，导致贴图即使存在也被冲白。新shader沿用原光照公式，**仅对可见灯罩的自发光表面**按PixelLab像素颜色调制并做 `radiance / (1 + radiance)` 压缩；不改变UV2间接光、房间照明能量、人物阴影或功率开关。灯带仍为连续低功耗蓝白照明，开关熄灭正常。灯带的表面明度因此比r12更柔和，具体观感仍待审图。

## PixelLab与可编辑文件

本轮三次官方 `/inpaint-v3` 请求：portal、lamp_a、lamp_b，每次实际10 generations，共 **30 generations**。提示词、干净导图、mask、固定seed、任务ID、原始PNG和实际用量均保存于 `source/`、`raw/`、`result_*.json`。没有上传Pixel Canals作品图像或账号凭证，没有自动重复POST。

母版以认可的r12四墙材质为底，仅增加后墙宽墙板替换层和灯带PixelLab材质层；不存在旧r6人工做旧回流。`source/assemble.py`负责裁切配准，`source/package.lua`导出Aseprite及PNG，`source/build_shader.py`保留shader变更入口，`source/review.py`检查范围并生成对比页。

## 验证边界

四墙改变只落在灯带／槽口范围及后墙门所在宽墙板；其他16种墙板安排未变。四份PNG与Aseprite回读逐像素一致，N颜色诊断及灯带断电／恢复的画面均精确恢复。实际Godot截图覆盖左中右游戏镜头、后墙和灯带近景、四角、灯带四个转角、显示实体的前墙及灯带开关。源检查见 [quality.json](source/quality.json)。

模型、UV、碰撞、相机、舱体、地板和既有烘焙数据保持；本次没有重烘焙新固有色的间接反射，不作为新完整光照包。灯带纹理与可见发光面的变化需用户审图后再定。
