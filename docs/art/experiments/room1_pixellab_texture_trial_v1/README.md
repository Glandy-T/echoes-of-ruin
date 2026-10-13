# Room 1 — PixelLab 网页贴图试验 v1

2026-10-13。用户要求先使用 PixelLab 网页试做贴图，根据结果再决定是否订阅。本轮在 Chrome 中操作已登录的 Web Creator，下载原始 PNG，在 Room 1 v1.1 的独立 Blender 副本中试贴墙面与地面。

**阶段判断：可以产生可试贴的基础颜色材质，但本轮结果仍不足以认定“低模3D + 接近2D像素作品”的整套美术路线已经成立。**

## 本轮实际结果

| 请求 | 模型 / 网页标示消耗 | 结果与使用方式 |
|---|---|---|
| 墙面第一次 | Pixen / 1 | 自动加入管线、通风结构和机械板，不采用 |
| 墙面第二次 | Pixen / 1 | 云状明暗、明显边框，不采用 |
| 墙面第三次 | Pro / 10 | 更克制的浅灰表面；采用左上候选的内部区域 |
| 地面第一次 | Pixen / 1 | 明显斜向裂纹和高光，不采用 |
| 地面第二次 | Pro Flash BETA / 5 | 深蓝灰、低对比像素颗粒，作为基础材质候选 |

5 次生成请求合计消耗 **18 次试用额度**。账户页实际显示从 **22/40** 变为 **40/40**。本轮未订阅、购买额度或改动账户设置。这里记录的是本次网页显示与实际消耗，不能推定今后的价格或每个模型都具有同一计费规则。

原始输出保存在 `textures/`，所有失败样本均保留。网页截图见 `evidence/pixellab_web_result.jpg`；精确提示词、参数和成本见 [`source/generation_record.json`](source/generation_record.json)。

## 图像与试贴参数

- Pixen 的三个输出均为原生 **128×128 PNG**；不采用的原因来自可见造型与画法，而非文件格式。
- Pro 设置单候选为 **128×128**，实际下载的文件是 **256×256 的2×2候选图**。整图读取到9种 RGBA 颜色。
- Pro Flash 下载的是 **64×64 PNG**，读取到44种 RGBA 颜色；提示中的“4至6色”并未严格实现。
- 原始生成图未重绘、滤镜处理或放大后再保存。
- 墙面使用 Pro 图左上候选的内部 **126×126 区域**，由 Blender 材质节点寻址并重复，避开候选图中线。完整原图保留，不把候选分隔线当墙缝。
- 墙面该区域覆盖4m，约31.5 texels/m；地面64px覆盖2m，32 texels/m。**这只是本轮对照参数，不是项目统一标准。**
- 图片以 sRGB 基础颜色输入，采样 `Closest`，沿用 v1.1 的审查灯光。原有 UV 保留，新增平面试贴 UV。

`source/image_inventory.json` 记录文件尺寸、颜色数量、透明度范围、散列和边缘差异。边缘差异只是描述数据，不能据此宣布无缝铺贴或视觉验收通过。重复铺贴仍应以镜头中实际看到的结果审查。

## 目视观察

- 普通材质图已能覆盖墙和地面，近景可见明确的块状像素；房间尺寸、20舱、门洞和占位门保持 v1.1 的状态。
- 浅墙与深地面维持了舱体轮廓可读性；地面已不再呈现第一次 Pixen 输出的裂纹。
- 墙面灰斑和地面小亮点存在明显的重复节奏，表面变化仍偏泛用材料颗粒；需要进一步决定这些痕迹的用途与密度。
- 基础材质没有形成完整的产品与建筑表面设计。休眠舱、玻璃和屏幕仍是灰模材质，尚未制作舱体像素色块、编号与状态信息。
- 原审查灯光保留了平滑的3D明暗。像素贴图自身不能替代受控光照、画面采样和游戏镜头的共同设计。

本轮只证明网页生成、PNG 下载和 Blender 材质应用流程实际跑通，并产生候选基础材质。只有一次 Pro 和一次 Pro Flash 对照，且提示不同，不构成普遍的模型质量排名。

## 底图引导的限制

已准备 `source/wall_color_layout_GUIDE.png`：固定底色与极少的颜色区域，用于限制材料画法。它是技术导引图，**没有用作生产纹理**。

Chrome 扩展的 `fileChooser.setFiles` 因“Allow access to file URLs”关闭而拒绝上传。本轮没有改变权限，也没有通过其他方式绕过该限制；所有生成均为纯文字输入，参考图计数为0。因此尚未验证 PixelLab 对项目底图、遮罩或 UV 岛边界的保留能力。

下一步应先解决用户选择的底图输入方式，再用一个舱体大面和固定色板检查结构、边界及明暗保留。当前结果不足以证明可自动处理完整 UV 图或精确文字。

## 文件与复现

- [对比预览](preview.html)：灰模、试贴全室、较低镜头、材质近景、原图与失败对照。
- [Blender 工程](room1_pixellab_texture_trial_v1.blend)：图片已打包，独立可打开。
- [应用脚本](apply_textures.py)：读取相邻 `room1_full_lowpoly_v1_1.blend`，另存本试验目录。
- [提示词与生成记录](source/generation_record.json)
- [原图清单](source/image_inventory.json)
- [底图生成脚本](source/prepare_guide.py)

在 Blender 5.0.1 后台运行 `apply_textures.py` 可重建试贴工程和三个渲染图。像素贴图为实际下载的AI输出，重新生成不会保证获得同样图案。本轮没有改动现有 Godot 工程或 FreeCAD 文件，也没有进行游戏运行或舱盖避让验证。

## 来源与归属

材料图由用户的 [PixelLab Web Creator](https://www.pixellab.ai/create) 账户生成，原始提示和参数随本目录保存。房间、休眠舱和来源说明继承 [Room 1 v1.1](../room1_full_lowpoly_v1_1/README.md)。

休眠舱的新低模网格参考 [Scifi - Cryogenic Sleep](https://sketchfab.com/3d-models/scifi-cryogenic-sleep-3e65d80f30fb4a9e81f721f1c0cb8474)，作者 [Artboard Silvio Pinheiro / scrpinheiro](https://sketchfab.com/scrpinheiro)，用户提供 GLB 许可元数据为 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。本作重建网格，修改为头部窗口、整片舱盖、有限开盖和脚端信息屏。原参考网格没有直接并入本工程。
