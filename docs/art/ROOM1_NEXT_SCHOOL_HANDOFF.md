# 学校交接：2026-11-04 继续门外场景

**2026-11-04执行更新：**已完成[走廊局部模块／墙板候选与镜头原型](experiments/cryo_corridor_sample_v1/README.md)，F6 `scenes/dev/cryo_corridor_sample_v1.tscn`。用户新暂定方案为出门黑屏后相机水平反转180°，邻室遮挡透明，返回室内恢复；候选内已实现并通过往返、方向及碰撞检查。PixelLab API已在学校验证，使用30次额度；墙板候选待审，地坪两次返回纯色未通过，已停止生成。没有完成全走廊、楼梯正式美术或1F室外出口，未迁移F5或推进主角3D。下面保留11月3日的原始开工交接。

更新：2026-11-03，日本时间。交接前成果基线为GitHub main `097847bc0dcccc667dbe7ef39ad03433ebc55599`；交接本身随后单独提交。本文为当前学校交接入口，替代原2026-10-30仅描述r19的旧状态，历史可查Git。

## 明天的优先事项

用户最新要求：先继续场景外部，不立即推进主角3D。**建议从现有4F门外走廊与消防楼梯的可走路线开始**，这是有灰盒和冻结工程依据的起点；“外部”尚未进一步锁为整栋外立面或园区室外大场景，不把本建议冒充新确认的制作范围。若转做真正室外，应先核定1F出口连接与可见范围。

1. 先拉取GitHub main，并读本文、[当前入口](../../从这里开始.md)、[版本索引](ROOM1_VERSION_INDEX.md)。学校已有修改时先检查、保留，再合并；不要强制覆盖学校成果。
2. 用Godot4.6.2打开根`project.godot`，等待完整导入。先F5确认原有流程，再F6运行最新美术工作集`scenes/dev/room1_door_window_r30.tscn`；两者目前并非同一套最新材质。
3. 从r30现有门外路线继续建立独立外部候选，保留Room 1已认可的墙地、舱体、门与灯。避免直接以旧route_v3整套场景的Room 1外观当最新室内基准。
4. 第一块建议完成4F门外走廊的低模建筑模块、UV和一个PixelLab材质样段，与Room 1门口同镜头检查衔接；认可后再扩展。随后按现行Brief推进楼梯间灯带与正式美术，不一次铺完整栋楼的贴图。
5. 保留当前纸片人物用于尺度、遮挡和移动。主角三视图存好后暂缓建模，3D角色不构成继续外部场景的阻塞。

这里是下一步计划，本轮交接没有生成外部资产或修改场景。

## 实际入口与文件

| 用途 | 当前入口／源 | 注意 |
|---|---|---|
| 正式游戏功能 | `project.godot` → F5 →「はじめる」；`scenes/areas/military_facility/cryo_room_4f_01_3d.tscn` | 继承r19：开场、移动、调查、暂停和自动认证路线已整合。没有在本轮切成最新室内材质。 |
| 最新Room 1完整美术 | `scenes/dev/room1_door_window_r30.tscn`，F6 | r24墙＋r26地坪＋r28全20舱＋r29哑光门面及r30认证窗去白边。正式F5入口迁移仍是单独工程步骤。 |
| 最新完整Blender | `docs/art/experiments/room1_door_window_r30/room1_door_window_r30.blend` | 依赖同仓库相对贴图，不是脱离仓库的单文件。Blender5.0.1制作。 |
| 门外可玩路线的原始记录 | `docs/art/experiments/cryo_building_room1_route_v3/README.md` | Room1→4F西南授权走廊→西梯4F至1F。原记录中的“旧门占位”等是当时状态，不覆盖r19/r30现行门。 |
| 路线GLB与控制 | `assets/art/cryo_building_room1_route_v3/room1_west_route_v3.glb`；`scripts/dev/cryo_building_room1_route_v3.gd` | r30脚本继承链仍包含它；现有外部识别材质／临时楼梯相机不是正式美术或灯光。 |
| 整栋与四梯Blender | `docs/art/experiments/cryo_building_stairs_v2/cryo_building_stairs_v2.blend` | 20层及四梯空间骨架；不是已完成的全楼游戏美术。 |
| 主角当前参考 | `docs/art/experiments/protagonist_turnaround_v2/` | `views/front.png`、`side.png`、`back.png`；`editable/`三份Aseprite；`parts.svg`部件标注。不是3D资产。 |

F5操作：WASD移动、E调查、Enter翻页、Esc暂停。F6的F1走廊／F2西梯入口／F3一层平台等属于审查跳转键；若当前候选改了快捷键，读对应脚本，不把审查跳转当正式玩法。学校机器的运行、导入、网络与灯光仍须当场验证，家里曾经通过不等于学校已验收。

## 外部场景不能跑偏的约束

- 尺寸／空间按[设施规格](../CRYO_FACILITY_LAYOUT.md)、冻结`docs/cad/cryo_standard_floor/v3_trim/floor_layout.json`、[整栋低模Brief](CRYO_BUILDING_LOWPOLY_BRIEF.md)。FreeCAD只作尺寸、坐标、关系参考；游戏低模建筑另做，不照搬CAD几何外观。
- 共20标准层：地上16层＋地下4层；每层48室、四个互不连通分区；西／东和北／南两组共四座消防梯。主角房SW-01只是技术锚点，不因房号未最终固定而停工。
- 可进入主角所在4F授权区域及消防楼梯；其他房间、其他楼层室内因芯片权限不可进入，省略内部。四座消防梯均可上下，不采用“4F向上坍塌”旧案。人员电梯紧急用电下停运，不能重新开启。
- 现有可玩测试路线止于1F西梯平台；**尚未确定／完成1F出室外连接**，不能声称已到室外。楼体外立面、屋顶、园区室外的最终造型也没有定稿。不恢复4F监护站／护士台旧设定。
- 楼梯照明按[运动感应应急灯带Brief](CRYO_STAIR_MOTION_LIGHTING_BRIEF.md)：比休眠室更明亮；无人时保留最低导向光，接近时整段梯跑／平台提前增亮，后方延时渐暗，停留时不能立即熄灭。高度、亮度、触发距离、渐变时长和正式楼梯镜头尚待小样实机确认；这仍不是已实现／验收的效果。
- 人员电梯入口按[电梯门／CAUTION Brief](CRYO_PASSENGER_LIFT_ENTRANCE_BRIEF.md)：只做可见关闭门体、无响应操作区与独立应急提示；不做轿厢、开门运行或楼层交互。具体门板候选未最终批准。
- Pixel Canals为技术观感硬参考；PixelLab做主体材质／做旧／差分，Aseprite可独立图层局部精修。原生密度、1280×720审图和最近邻等按[像素基准](PIXEL_ART_PRODUCTION_STANDARD.md)，不重新开始像素大小无目标迭代。其NoAI图像不上传生成服务。
- 修改UV、几何、光照或材料时执行[光照／UV检查](ROOM1_LIGHTMAP_QA.md)，分开报告技术通过、实际画面和用户认可；不能只核对哈希就宣布完成。

## 今天保存的主角状态

- 正面`protagonist_front_v2`获用户认可为继续制作的工作基准：年轻女性、深色长发、简单白色统一休眠袍、浅肤色、弱化五官。具体3D后还会调整，不是最终模型定稿。
- `protagonist_turnaround_v1`背面手脚被用户指出仍按正面画法，**该背面不可作为建模依据**。当前使用`protagonist_turnaround_v2`，只用PixelLab返修四个手脚区域，其余与正／侧面保持。
- 返修后已看原图和放大局部，并独立复查。手指弯曲比侧面略大、脚略外撇，统一3D体积时还需校正；用户之后说“好吧，先写交接”，不把它扩大成最终解剖／模型批准。
- 后续部件按身体（头颈／手脚）、独立连续白袍、少量前发／后发体块规划，一个骨架驱动；尚未生成3D、分网格、UV、绑定或替换Godot纸片占位。
- 最新来源与限制见[三视图v2 README](experiments/protagonist_turnaround_v2/README.md)和[角色Brief](PROTAGONIST_LOW_POLY_BRIEF.md)。给3D生成器时使用独立无标注视图，避免上传多个人物并排的工程排版图。

## 在学校电脑使用PixelLab

**可以继续用；生成不依赖家里的Aseprite插件。首次换电脑的凭据／网络与已有运行环境仍需核对，不承诺学校尚未验证的连接已经成功。**

| 方式 | 学校需要什么 | 是否额外安装 |
|---|---|---|
| 网页生成／浏览器编辑器 | 浏览器、登录自己的PixelLab账户、可访问服务的网络 | 无需安装Aseprite或PixelLab插件；简单网页功能与完整编辑器不完全相同。 |
| 今天实际使用的Python API直连 | 仓库脚本、可用Python运行环境、自己的访问令牌；导图／图像脚本通常还用Pillow及NumPy | 不需要PixelLab SDK、Aseprite生成插件或接管桌面；若学校运行环境缺Python／图像库，仍需补齐，先检查再决定。 |
| Aseprite内生成／局部精修 | 本机Aseprite；若要在其内生成，再安装PixelLab扩展及完成权限／账户连接 | 新机器的插件安装与权限不会随GitHub自动恢复；只做API生成不必走这条路。Aseprite局部精修仍需要该编辑器本身。 |

今天的连接帮助代码已上传，例如`docs/art/experiments/protagonist_turnaround_v2/source/pixellab_api.py`。优先读取本地环境变量`PIXELLAB_API_TOKEN`；家里当前也可回退读取本机Aseprite扩展的私有配置。**该私有配置和令牌没有上传GitHub，学校拉取项目后不会自动获得授权。**在学校本机安全配置自己的令牌即可沿用账户；不要把令牌粘进交接、Git、截图或公开聊天。

学校执行者先检查Python能否导入`PIL`、`numpy`，再用只读`GET /v2/balance`验证账户连通和额度；不要以重新运行历史付费生成任务来测试连接。已有任务状态／ID要保留，状态不确定时先查询，不盲目重发POST。新生成仍消耗账户额度，不是换电脑后另有免费额度；可用功能、权限和余额以同一账户当时实际显示为准。

学校无需复用家里`C:\Users\Glandy`或G盘路径；脚本以仓库位置解析路径，凭据、Godot／Blender／Aseprite路径按学校实机配置。今天的localhost预览端口只在家里当前服务存活时有效，学校直接打开仓库`preview.html`或在学校重启对应`source/serve_preview.py`，不要把127.0.0.1链接当GitHub在线站点。

官方资料核对于2026-11-03：[使用方式](https://www.pixellab.ai/docs/ways-to-use-pixellab)、[Aseprite安装](https://www.pixellab.ai/docs/installation)、[API文档](https://api.pixellab.ai/v2/docs)。

## 本轮交接的边界与恢复

- 本轮只写交接和更新入口，未制作外部资产、未迁移F5、未改室内或角色素材、未测试学校机器。
- 本机历史归档／稀疏检出规则见[本机交接](LOCAL_WORKSPACE_HANDOFF.md)。旧名称依赖仍可能被现行场景加载，不能按编号一律删；完整Blender需同仓库相对资源。
- GitHub交付按项目约定默认上传。学校继续后也保留可编辑源、必要导出、PixelLab实际输入／输出／用量与真实同机位效果，完成后同步main并核对远端。

## 复制给学校Codex

> 请先拉取并阅读GitHub main最新的`docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md`和当前AGENTS.md。今天先继续外部场景，建议从现有4F门外走廊与西消防梯路线的小样推进；保留Room 1 r30及其他已认可室内资产，暂缓主角3D。先核对冻结CAD和现行楼梯／电梯Brief；1F真正室外出口尚未确定，不虚构完整出楼路线。PixelLab继续主体制作，Aseprite可独立图层局部精修；先检查学校运行环境，并在本机配置账户令牌、只读验证连接，密钥不要写入Git。不要沿用旧三视图v1的错误背面。开工前检查本机修改并保留已有学校成果，不强制覆盖。
