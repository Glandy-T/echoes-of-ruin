# 现成后发 + 两束耳前发 v4（静态外观待审）

2026-10-13。用户选中 Jan Bláha 的 Long hair variants 最右侧直发角色，
要求在耳前增加两束落到胸前的头发，保留原后发轮廓。

## 本轮成果

- `00_comparison.png`：同一相机、同一材质环境下的原后发 / 加前发对照，实际 Blender 渲染。
- `02_front_locks.png`、`03_front.png`、`04_side.png`：修改后的近正面、正面、侧面。
- `05_back.png`、`06_hair_isolated.png`：背面及独立头发。
- `hair_front_locks_v4.blend`：可编辑原型。主场景为 `SOURCE_SCALE_HAIR_REVIEW__STATIC`，另有对比场景。
- `build_hair_preview.py`：从原始 Blender 文件重建的脚本。

本轮沿用来源角色作为试戴参照，便于看清发型改动。**这不是已经适配到 165 cm 人体的角色成品。**
参考人物的五官、卫衣和肤色不作为主角设定。源 `.blend` 的同款人物衣服材质是蓝色，
预览中改为锈红色以接近用户提供的 Sketchfab 截图；所有预览之间保持一致。
此前选中的白袍仍保留候选状态，尚未购买或处理。

## 网格分离和来源

| 可编辑对象 | 顶点 | 三角面 | 内容 |
| --- | ---: | ---: | --- |
| `Hair_Back_SOURCE_UNCHANGED` | 119 | 236 | 原 `Plain.001` 的镜像评估结果，仅移到 X=0；原轮廓保留 |
| `Hair_Front.L` | 48 | 92 | 新增左前发，从耳前顺至胸前 |
| `Hair_Front.R` | 48 | 92 | 新增右前发，末端略有长度差 |
| 合计 | 215 | 420 | 三个独立网格，未与身体合并 |

前发采用少量有厚度的面，与原后发保持简洁的几何语言。根部藏入原侧发，保留脸部和颈部的开口。
后发与前发之间的重叠是独立发件的连接方式，不是焊接；后续绑定时仍须检查根部是否露缝。

来源：**[Long hair variants](https://sketchfab.com/3d-models/long-hair-variants-e667cad434c84cb6bd567c62ed54de48)**，
作者 **Jan Bláha（swifterik）**，**[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)**。
原始 ZIP 和 Blender 文件未修改，署名、来源和 SHA256 见 `source/ATTRIBUTION.md`。
本项目改动为提取该款头发、新增左右前发、创建草案 UV 和制作对比预览；无原作者背书。

## UV、绑定与验证范围

来源审计确认：原后发有名为 `UVMap` 的层，但全部 UV 三角面积为零，不能绘制有效贴图。
其材质只有颜色，没有贴图。源文件也没有骨架、权重或动作。

本轮保留原 UV 为 `UV_Source_Preserved`，为三件头发另建共同使用的 `UV_Pixel_Draft` 草案图集，
并将其设为活动及渲染 UV。独立复核结果与草案 UV 图见 `validation/`。
三件头发的活动 UV 均在 0–1 内，无零面积三角形，无对象内部或跨对象的正面积重叠（含完全包含检测）。
后发内侧的两个面使用独立凸 UV 岛，避免自动投影折叠；草案图集为它们保留了底部区域。
该 UV 是后续绘制的起点，**没有冻结纹理分辨率、像素密度或最终 UV 岛排布**。
当前渲染为纯色材质，尚未制作最终像素贴图。

已复核后发的顶点、面连接和原轮廓未变，最大坐标差约 `2.98e-8 m`（浮点误差）。
左右前发均为闭合网格，没有退化三角形或法线绕序冲突。
原后发自带 **1 条非流形边**，本轮保留并记录，正式适配和绑定前需要处理，不能称为完整生产检查通过。
两束前发各与后发产生 24 对三角形相交，发生在发件叠放连接处；左右前发之间不相交。
这些数值用于定位独立发件的重叠，不能替代转头、贴合人体或动画时的穿插检查。

**仍待完成：** 外观确认；适配 pistachio 165 cm 人体；正式发骨 / 权重；转头、迈步、蹲下及白袍穿插检查；
目标游戏镜头和 Godot 运行验证。不能把静态造型与 UV 检查视为动画验证通过。
人体 v2.1 已知的身体 UV 重叠仍是独立问题，本轮没有修改人体文件。

## 重现

在 Blender 5.0.1 中使用 `--background --factory-startup --disable-autoexec --python-exit-code 1 --python build_hair_preview.py`。
脚本通过 `use_scripts=False` 打开源文件，不执行下载文件内的脚本。
验证脚本位于 `validation/`；源文件库存脚本和报告位于 `audit_source/`。
验证时先加载文件：`--background --factory-startup --disable-autoexec hair_front_locks_v4.blend --python validation/validate.py`。

所有内容是版本化待审草案，没有覆盖或替换游戏中的角色资产。
