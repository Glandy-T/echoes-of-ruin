# 学校交接：2026-11-06／主角分件生成与动作准备，4F v6仍待选

**当前优先：主角分件候选与绑定前检查。** [总入口](experiments/protagonist_tripo_robe_v2/preview.html)提供身体 v1、白袍 v2 各自的 Blender、原始导出、正侧背与斜视图。用户已要求为换装把身体和衣物分开，并明确考虑后续绑骨运动。白袍文字 v1 附带手脚，已拒绝；灰模正反面引导的 v2 成为衣物候选。手工结构 v3 因源衣服腋下本身自交，已停止继续修补，保留失败证据。

**尚未完成：**新身体脚趾局部28对相交需要简化；新白袍v2有272对相交和2条非流形边，虽开口成立，仍仅作外形候选。先重新整理衣服腋下／内外层变形拓扑并重查，不能直接自动权重。之后统一身体和衣服的身高、关节与休止姿势再试穿，用共享骨架做抬臂／弯肘／行走变形检查，最后才固定UV和PixelLab贴图。没有正式绑骨、权重或动画验收，未替换游戏角色。头发v2仅作为当前发型来源，未装到新身体。

**楼梯材质仍待审：**[局部折中候选](experiments/cryo_stair_material_sample_v1/preview.html)沿用 r24 墙、灰色矿物踏步＋平台。首轮偏花，quiet1过平，当前只作局部折中，不是认可基准。Godot入口 `scenes/dev/cryo_stair_material_sample_v1.tscn`，F6、1/2/3机位。整栋推广及最终运动灯光未完成。

**历史主角试作，只供追溯：**[本地修模v1](experiments/protagonist_blender_cleanup_v1/README.md)被用户否决；[免费H2.5](experiments/protagonist_tripo_h25_v1/README.md)有后发碎片、无UV／骨架；[国际版P2.0免费试作](experiments/protagonist_tripo_trial_v1/README.md)当时无法下载。旧暂停已被11月6日恢复制作指令取代，旧模型否决并未撤销；不要将这三个版本混入当前国内版原始源。

**4F路线仍停在v6待选。** 镜头、触发方式和显现强度尚未由用户选定，也没有迁移正式F5。主角检查不自动确认或改动该路线。

交接前成果基线：[GitHub main 732f226](https://github.com/Glandy-T/echoes-of-ruin/commit/732f2268b4668184160b8d58bfb7177b890b6daf)。本交接随后单独提交。此页已合并11月4日进展，替代原来层层追加的旧计划；11月3日及早期交接可从Git历史追溯。

## 接手后先做什么

1. 检查本机`git status`并保留已有差异，再同步main。下面列出的未提交文件不能清理或顺手混入本次提交。
2. 当前先打开[身体／白袍分件候选](experiments/protagonist_tripo_robe_v2/preview.html)，确认人体比例、袍型及真正开口；结合静态QA定位问题，再统一姿势、试穿并临时绑骨。不得使用失败的手工 v3 或文字白袍 v1 直接继续UV／贴图；原整人头发v2留作造型来源。
3. 4F路线另看[五种镜头、两种触发和四段动图](experiments/cryo_4f_camera_compare_v6/preview.html)。Godot打开`scenes/dev/cryo_4f_camera_compare_v6.tscn`，F6运行，F8到走廊；不要用F5判断实验。
4. 等用户确定v6镜头、触发和显现强度后再收敛，不把默认A／距离规则／50%当成已认可方案，不改回人物周围挖洞。
5. 楼梯材质仍是局部折中候选，运动灯光未实现；1F室外连接未确定。主角当前已恢复并走分件候选路线，旧暂停记录只供追溯。

## 用户最新要求与已改变的方向

- 相机可以前移、缩小透视视角来放大构图，或适当组合，尽量减少多余空房间占画面；**相机仍留在前侧墙外，不越墙进入狭窄走廊。**
- 前侧墙和门平时隐藏；主角靠近一定距离，或进入门前区域时，相应门墙整段渐显，离开后渐隐。两种触发都做成对比，注意是否挡住人物、是否在边缘闪烁。
- **不采用人物周围局部挖洞消隐。** 此前查阅Trifox等案例时提出的局部溶解只是讨论建议，已被用户这次明确要求替代。
- v5“整面常驻42%半透明”保留为旧对照，不能把它当作v6的当前目标。
- 其他47间房先不做休眠仓或室内；Room1保留已有20舱。门后灰色场景本轮不处理。
- 门先按E才开始认证；主门成功后开门，再对双面黑门洞按E进出，全黑时换位并转镜180°，返回恢复室内镜头。
- 其他仍工作的认证门按E后小窗黄闪，权限不足后红灯拒绝，保持关闭；不用弹窗替代灯语。停运电梯按其独立Brief保持不认证，不套黄／红灯。

## 当前入口，别混版本

| 用途 | 入口 | 实际状态 |
|---|---|---|
| 本次优先比较 | `scenes/dev/cryo_4f_camera_compare_v6.tscn`，F6 | 独立镜头＋接近显现实验，尚未选定组合。 |
| 旧4F整层候选／v5 | `scenes/dev/cryo_4f_complete_v3.tscn`，F6 | 文件仍叫v3，但逻辑已经包含v4灯语、v5横移及单门目标修正；42%常驻半透明旧对照。 |
| 最新室内美术 | `scenes/dev/room1_door_window_r30.tscn`，F6 | r24墙、r26地坪、r28全20舱、r29门面及r30认证窗局部精修。 |
| 正式游戏 | `project.godot` → F5 →「はじめる」 | 仍是r19正式功能入口，未换成本轮v6；原靠近自动认证／行走路线与实验E流程有区别。 |

旧v1实时小样、v2局部烘焙、v4／v5修正截图都只供追溯。当前整层资产仍在`assets/art/cryo_4f_complete_v3/`；版本数字不代表可以删除依赖。

## v6怎么比较

| 按键 | 功能 |
|---|---|
| 1–5 | 切换A–E镜头，不改变人物位置。 |
| T | 沿墙距离／门前区域触发。 |
| R | 50%半显／100%实体遮挡对照。 |
| F7 | 自动／强制隐藏／强制显现，HUD显示当前状态。 |
| F8／Home | 到走廊门外／回室内。 |
| F11／F12 | 整层俯视／技术切区，不授予正式玩法权限。 |
| E | 沿用门认证、拒绝及黑门洞进出。 |
| F9／F10 | 灯带／raw与降噪光图对照。 |

镜头方案只用于八条水平走廊。室内、连接廊和楼梯沿用原镜头；在室内按1–5不会改变室内构图，先按F8进入比较。

| 方案 | 距离／水平FOV | 高度 | 代表机位下方空白 | 实测纸片角色高度 |
|---|---|---|---:|---:|
| A 原构图 | 8m／50° | 2.2m | 22.63% | 232px |
| B 前移 | 6m／50° | 2.2m | 10.50% | 302px |
| C 缩小视角 | 8m／38.5° | 2.2m | 13.45% | 310px |
| D 适度组合 | 7m／44° | 2.2m | 12.58% | 304px |
| E 更近构图 | 4m／50° | 2.2m | 0% | 423px |

空白数据只对应同一走廊中线点x=16m、z=-10.7m、前墙隐藏的画面下方；**不能说E在所有位置都没有空白**。角色高度由固定帧图对测量。B/C/D放大程度接近；E更紧，角色和像素也明显变大，周围可见范围变窄。

显现规则：进入距离1.15m、退出1.35m；门前区域还要求左右距门中心≤1.2m，离开到1.5m外才释放。离开保持0.20s后渐隐，显隐各约0.28s。段长暂按冻结房间左右边界约21m，共32组前侧门墙；这是实验分组，尚未作为最终表现批准。

认证中的门在原交互范围内会保持显示，便于读小窗。当前互动提示仍沿用原1.5m范围，可能早于自动显现阈值出现；选定主方案后再一起审看这处衔接。

**已经看清的取舍：**100%实体从墙外看会完全挡住人物，保留作反例；50%单层显现保留约50%人物图像对比度，仍会压暗人物。这不是用户已认可50%的结论。距离触发沿墙横走仍显现；区域触发离开门前后隐去，二者都保留待选。

## 已验证到什么程度

- [功能报告](experiments/cryo_4f_camera_compare_v6/functional_validation.json)：PASS。120组位置＝5镜头×8走廊×3纵向位置；都在前侧墙外，最小实测墙外余量约1.69m，人物投影在画框内。
- 隐藏墙、相邻门和分区门仍有碰撞；保留原469个整层新增碰撞体，32组显示层不改变物理网格。
- 原主门认证开门、第二次E黑屏换镜、返回室内原8m／50°相机，对门黄闪红拒绝、无权限弹窗取消均通过。
- 距离阈值、门前区域侧边、跨房间段边界的往复测试，没有反复开关显隐。
- [实机图、4段运动GIF](experiments/cryo_4f_camera_compare_v6/preview.html)包含靠近／退开及沿墙横移；另有7张认证与往返实拍。截图1280×720，GIF精确缩半并使用共享调色板，原PNG和模拟时间保留。
- 捕获使用`--fixed-fps 60`，不是学校机器真实FPS结论。没有做其他机器的性能或新楼梯镜头验收。

上述是技术和画面检查，**不是用户认可最终方案**。下一轮先让用户比较，不继续无目标地改透明百分比或抽材质。

## 这一层及美术做到哪里

- 冻结布局48间房外壳、8条走廊及侧廊／连接节点已接入。其他47间没有舱体、可进入室内或室内地坪；Room1仍是既有20舱。
- 整层复用r24墙板及r26中央过道地坪裁片，避开舱位痕迹；取消过往重复独立灯管。门继续沿用r30素材。
- 整层v3已完成Cycles 4096采样、4096²图集烘焙，光照16px/m，原生颜色以80px/m为基准。当前GLB、映射和HDR由清单配套；raw经过连续UV2重投影但未降噪，未重投影的Cycles输出另存为`source_*.exr`。不能把它写成未经重采样的原始文件。
- v6只改显示和比较控制，未改像素颜色、UV或静态光图，也没有新生成材质。仍遵守[光照／UV检查](ROOM1_LIGHTMAP_QA.md)。
- 西梯既有4F至1F路线保留，东／南／北有4F入口灰盒。楼梯、公共区专用门型、电梯入口、外立面均未完成正式美术。1F到室外的连接尚未确定，不能声称已做完整栋或已走到室外。
- 其他房间和楼层权限不开放，F12只是审图跳转。停运电梯不恢复运行。楼梯后续读[感应灯带Brief](CRYO_STAIR_MOTION_LIGHTING_BRIEF.md)，电梯读[入口Brief](CRYO_PASSENGER_LIFT_ENTRANCE_BRIEF.md)。
- 主角仍为临时纸片，受光沿用已有近似；[三视图v2](experiments/protagonist_turnaround_v2/README.md)和[主角Brief](PROTAGONIST_LOW_POLY_BRIEF.md)保留，已取得3D分件候选，未完成绑定／替换。不要把旧v1错误背面当建模依据。

## 主要文件与复现

| 内容 | 文件 |
|---|---|
| v6逻辑 | `scripts/dev/cryo_4f_camera_compare_v6.gd` |
| 原场景裁切／单层门墙显示 | `scripts/dev/cryo_4f_camera_context_v6.gdshader`、`cryo_4f_camera_section_v6.gdshader` |
| 比较参数、限制和操作 | [v6 README](experiments/cryo_4f_camera_compare_v6/README.md) |
| 数值、逐图相机与显隐记录 | `docs/art/experiments/cryo_4f_camera_compare_v6/comparison_analysis.json`及`evidence/`中的JSON |
| 完整功能验证 | `scenes/dev/cryo_4f_camera_v6_verify.tscn` |
| 静态／运动／人物遮挡捕获 | `scenes/dev/cryo_4f_camera_v6_capture.tscn` |
| 认证与往返捕获 | `scenes/dev/cryo_4f_camera_v6_auth_capture.tscn` |
| 生成审图页与测量 | `docs/art/experiments/cryo_4f_camera_compare_v6/analyze_preview.py`，需Pillow／NumPy |
| 整层运行资产／烘焙源 | `assets/art/cryo_4f_complete_v3/`；[整层v3源与复建](experiments/cryo_4f_complete_v3/README.md) |
| 冻结尺寸 | `docs/cad/cryo_standard_floor/v3_trim/floor_layout.json`；[设施布局](../CRYO_FACILITY_LAYOUT.md) |

11月4日学校机曾使用并核对以下路径（历史环境记录；本轮家中工作区为 `G:/卒業制作/echoes-of-ruin`）：

- Godot：`E:/卒業制作/GODOT/Godot_v4.6.2-stable_win64_console.exe`。
- Blender：`C:/Program Files/Blender Foundation/Blender 5.0/blender.exe`，附带Python在`5.0/python/bin/python.exe`。
- Pillow／NumPy补充包：`E:/卒業制作/.runtime/python-packages`，运行Python分析时设置该`PYTHONPATH`。
- 当时CLI运行使用`APPDATA=E:/卒業制作/.runtime/roaming`、`LOCALAPPDATA=E:/卒業制作/.runtime/local`；这是学校代理的验证运行环境，不要求用户手工逐步配置。换机器先核对实际路径。

需要重跑时由接手代理执行对应验证／捕获／分析；只改交接无需重烘焙。旧日志中的系统根证书读取提示不等于本轮断言失败，判断应读PASS报告及实际画面。

## 本机未提交状态，必须保留

交接开始时已存在以下差异，本轮不处理，也不混入交接提交：

- `project.godot`：删除了两行显式默认配置`window/size/resizable=true`和`window/stretch/aspect="keep"`，其余本次不碰。
- 未跟踪`ASSET_CREDITS.md`。
- 未跟踪`assets/art/room1_integrated_door_v3/room1_integrated_door_v3_door_front.png`。
- 未跟踪`assets/art/room1_open_hero_bake_r1/strip_irradiance.exr`。

学校曾使用独立上传副本`E:/卒業制作/.publish-4f-complete-v3-20261104/`；11月6日家中按相同原则在当前仓库 `.delivery_uploads/` 下隔离提交。不要强制检出或清理这些未提交文件；换机器先看状态再拉取，不覆盖学校或家里的其他成果。

## 工具与生成额度

学校PixelLab API本轮早期已验证并实际调用；最初v1小样累计使用30次生成额度，地坪两次纯色未通过后停止，后续改为复用室内素材。v2至v6没有新增PixelLab生成。换机器或下次真正要生成时再核对连接，不把本轮成功写成永久可用。

没有必要为下一步比较镜头再生成贴图。用户不熟悉令牌配置，不要要求其在聊天里发送令牌或反复手动配置；先由代理检查可用工具与本机安全配置。Pixel Canals为技术观感参考，其NoAI截图／模型／贴图不得上传生成服务；PixelLab主体材质与Aseprite局部精修约束继续遵守。
