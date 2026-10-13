# Room 1 墙面像素贴图候选 v1

2026-10-13。按已确认 [墙面 Brief](../../ROOM1_WALL_TEXTURE_BRIEF.md) 制作，等待审图。旧纯色版完整保留。

## 本轮内容

- `#D3D6C9` 暖灰／象牙白主墙面，`#E7E7D4` 亮部，`#C1C8BC` 暗部；细腻哑光矿物／陶瓷复合质感。
- 连续墙面和少量必要收边；下沿窄金属保护带，局部旧接触擦痕、真实墙角与下沿积灰。
- 靠墙顶嵌入的窄白色灯带，穿过门上方，四面内墙同高度连续；没有断光段或新增外露灯具。
- 主墙面保持低对比，细节集中在灯槽、保护带、收边和材料色差；未加入满墙板缝或随机噪声。
- 本轮不加编号、出口文字、面板或其他设备。

配色、材质、连续保护带和灯带方向由用户确认；图像效果、保护带高度、灯带宽度、像素密度和实际亮度仍需本轮审图，不声明最终通过。

## 预览与可编辑文件

- [对比预览](preview.html)：纯色基准／墙面候选，低角度和正面材料近景。
- [Blender 工程](room1_wall_pixel_v1.blend)：8张墙面图已打包，可独立打开。
- [全室](evidence/01_wall_overview.png)、[低角度](evidence/02_wall_low_angle.png)、[正面材料近景](evidence/03_wall_detail.png)：均1920×1080。
- [后墙展开图](evidence_wall_elevation.png)、[材料像素3倍预览](evidence_wall_material_nearest3x.png)。展开图中的门洞区域由实际几何裁掉，不代表另做一片门。
- 分层 Aseprite：[后墙](editable/rear_wall_pixel_v1.aseprite)、[前墙](editable/front_wall_pixel_v1.aseprite)、[左墙](editable/left_wall_pixel_v1.aseprite)、[右墙](editable/right_wall_pixel_v1.aseprite)。
- [贴图与参数](textures/manifest.json)：四墙颜色图和独立发光遮罩。前后墙1680×272，左右墙728×272；80 texels/m只为当前墙面候选，不锁定全项目密度。

母版包含：AI 材质整理、连续收边／金属保护带、真实墙角／旧接触痕迹、连续灯带颜色、隐藏的发光遮罩、原始 AI 参考和底图。改发光强度只需调整遮罩／材质，无需改墙面颜色图。

## PixelLab 实际生成及人工整理

通过 [官方 Pro 编辑接口](https://api.pixellab.ai/v2/docs) 执行1次原创底图编辑，400×272px，实际返回图像并扣 **15次订阅额度**。调用前后余额差额一致，未充值；不上传账号余额或密钥。记录见 [任务结果](source/job_status.json)。

输入：[原创底图](guides/wall_layout.png)、[提示词](source/wall_edit_prompt.txt)。没有提交 Pixel Canals 图片、模型或贴图。原始返回：[wall_pro_00.png](raw/wall_pro_00.png)。

AI 保留了整体材质方向，但缩短灯带两端，并在输入段两侧画出磨损边框。本轮整理移除这类重复边框，将灯带恢复为连续窄带；以指定色板整理材料色阶，在房间实际墙角和保护带旧接触处安排局部痕迹。固定灯槽、保护带与发光遮罩由项目脚本独立绘制，未把人工完成部分称为原始 AI 输出。

最终候选使用四墙专用图，后墙三个原 mesh 共用一张连续展开图，门上方灯带的高度与左右墙一致。几何承担房间轮廓与门洞，颜色图承担材料、收边、有限老化；发光遮罩承担灯带亮起的区域。

## 范围与实际读回

源工程：`../room1_wall_floor_solid_v1/room1_wall_floor_solid_v1.blend`。原有136个对象的顶点、拓扑、变换和显隐保留，所有原UV层保留；仅六个墙面对象增加内侧平面UV和材质。地板、休眠舱、门、灯光和原相机沿用。额外增加一个正面材质审查相机，位于墙前近处，帮助看到不被舱体遮挡的保护带；不是游戏镜头。

[结构读回](structural_readback.json) 记录上述比较结果。实际输出并查看了全室、低角度及材质近景；Aseprite母版已通过批处理保存。结构检查、渲染和用户审图是不同层次，当前没有 Godot 运行验证。

**灯光边界：**这次完成的是灯带颜色与低强度材质自发光，Eevee 中并未加入向全室投光的灯对象；原有审查照明较亮。图像用于比较墙面，不能当作最终应急环境亮度验收。Godot 中灯带如何照亮人物和地面仍待后续实现。

## 复现

1. Python `source/prepare_wall_guide.py` 生成原创底图。
2. `source/pixellab_wall_job.py` 可查询已记录任务；`submit` 只有首次会发起付费请求，存在任务记录时拒绝重复提交。该脚本沿用相邻直接API helper；优先本机环境变量，显式读取已连接官方扩展的同服务凭证，密钥不写入文件。
3. Python `source/finish_wall_maps.py` 用已保存 raw 整理像素图，无额外生成费用。需要 Pillow、NumPy。
4. Aseprite批处理执行 `source/package_wall_masters.lua`，参数 `root=本目录`，保存分层母版及颜色导出。
5. Blender后台执行 `apply_wall_materials.py`，另存工程并出图；可加 `-- --reuse-baseline` 复用已有基准截图。

原始AI图、母版、颜色导出均已保存；重新导出不需要再次付费调用。脚本不含密钥，跨电脑生成需本机账号配置。

## 来源

- 时间线：[WORLD_BIBLE](../../../WORLD_BIBLE.md) 约80～90年休眠、约70年以上无人期；清扫停止年份TBD。
- 材料与老化：[ART_DIRECTION](../../../ART_DIRECTION.md) 第15–16节；具体未来复合材料的寿命无法仅凭年数计算，当前老化为有依据的美术推演。
- 方法参考：[Pixel Canals 研究](../../PIXEL_CANALS_REFERENCE.md) 和已认可的 [单舱v2基调](../room1_pixellab_pod_trial_v2/README.md)。
- 休眠舱保留源工程的自建低模；轮廓参考 [Scifi - Cryogenic Sleep](https://sketchfab.com/3d-models/scifi-cryogenic-sleep-3e65d80f30fb4a9e81f721f1c0cb8474)，作者 [Artboard Silvio Pinheiro / scrpinheiro](https://sketchfab.com/scrpinheiro)，GLB许可元数据为 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。重建与头部窗口／整片舱盖／有限开盖／脚端屏为项目修改，原参考网格未直接并入。
