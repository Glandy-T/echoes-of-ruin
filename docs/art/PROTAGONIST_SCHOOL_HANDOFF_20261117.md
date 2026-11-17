# 主角制作学校交接｜2026-11-17

**交接停点：L2 正面黑剪影已认可，正面两色体块已交、待用户确认。** 11 月 18 日到学校先看这张两色版，不自动当作定稿，也不直接生成 3D。

本次交接前的已发布成果为 [`ad51a88`](https://github.com/Glandy-T/echoes-of-ruin/commit/ad51a8880122be896bea3f8755aaa0dc9f039b5a)。明天同步的是包含本交接在内的最新 `main`，不必回退到该提交。

## 到校先做

1. 在学校项目根目录先看 `git status --short --branch`，再 `git fetch origin main`。干净且可快进时用 `git pull --ff-only origin main`；如有本机修改或分叉，先保留、比较，不执行硬重置或覆盖。
2. 读[重设计简报第 4 节](PROTAGONIST_REDESIGN_BRIEF.md#4-选定档位之后的顺序)和[当前待定清单](PENDING_DECISIONS.md)。简报优先于旧侧面诊断 S1～S3、v4／v5 和旧长发／长袖规格。
3. 打开[正面两色版审图](experiments/protagonist_l2_front_twotone_v1/preview.html)。GitHub 页面不直接运行 HTML 时，在学校本地打开，或直接看[并排 PNG](experiments/protagonist_l2_front_twotone_v1/evidence/silhouette_twotone.png)。所有图像随仓库提交，审图不需要登录生成服务。
4. **先由用户确认两色体块。** 若需改动，只改认可剪影内部的亮暗分区，不挪外轮廓。用户确认并要求继续后，再做正面成品上色。

## 哪些已经确定

| 项目 | 当前有效决定 |
|---|---|
| 简化档位 | 用户选 **L2**。约 6 头身，身体与四肢为简单体块；连指手套＋拇指、整块脚。不是 L1 写实，也不是 L3 大头。 |
| 当前阶段一造型 | 短发、短袖及膝休眠服、赤脚。此阶段不恢复长袖、长发、略挺的直筒外套感。 |
| 正面外形 | 用户已认可 `protagonist_l2_front_silhouette_v1`：衣身略呈 A 字，发顶有弧度，发梢略乱。后续正面内部绘制必须锁住这张剪影。 |
| 像素与尺寸 | 原生 **128×128**，人物可见高度 **117 px**，头部高度 20 px（5.85 头身）；头顶 y=6、脚底最后一行 y=122。衣身腰宽 23 px、下摆宽 31 px。放大用整数倍、最近邻，不做抗锯齿。 |
| 工作顺序 | 剪影 → 两色体块 → 成品上色。当前只推进到正面两色待审。侧面、背面另审，三视图认可后才进入 3D。 |

## 本轮两色版是什么

只使用 L2 比较稿沿用的两个中性研究色：亮 `#DADDD8`、暗 `#4F5E63`。它们用于看体块，**不是已经定好的肤色、发色与衣料配色**。

头发是暗块；面部开口保持单一亮色。衣服留连续大亮面，右侧暗面顺着微 A 字展开；袖下和四肢有简单暗面。没有眼部阴影、五官、P12、腕带、腰带、装饰褶或做旧。衣料最终材质、配色和时间痕迹还没有在这一步完成。

这是简报中的简单体块研究，不是最终像素贴图。此次没有调用 PixelLab、Tripo 或其他生成服务，未消耗生成额度。不能据此推断账户当前剩余额度或订阅有效期。

## 文件入口与来源

路径均相对仓库根目录；学校盘符不要求和家里一致。

| 用途 | 文件 |
|---|---|
| 当前待审两色 PNG | `docs/art/experiments/protagonist_l2_front_twotone_v1/front_twotone.png` |
| 两色版可编辑源 | `docs/art/experiments/protagonist_l2_front_twotone_v1/editable/front_twotone.aseprite` |
| 两色并排审图 | `docs/art/experiments/protagonist_l2_front_twotone_v1/preview.html` |
| 已认可、需锁定的轮廓 | `docs/art/experiments/protagonist_l2_front_silhouette_v1/front_silhouette.png` |
| 已认可剪影分层源 | `docs/art/experiments/protagonist_l2_front_silhouette_v1/editable/front_silhouette.aseprite` |
| L1／L2／L3 历史比较 | `docs/art/experiments/protagonist_simplification_l123/`；用于追溯 L2 选择，不再开三档重选 |
| 本轮范围与核验 | 两色目录下的 `README.md`、`source/manifest.json`、`source/validation.json` |

两色 Aseprite 有两个可见层：亮色基底、暗色体块；第三层是隐藏的认可剪影参照。认可剪影本身另有分层母版，保留旧 L2 隐藏参照。本轮没有覆盖任何旧来源文件。

核验已完成：两色版透明度与认可剪影逐像素一致，**外形差异 0 px**；全图恰好两色；Aseprite 保存后回读与 PNG 的可见像素一致。已打开并检查全身与头部／衣身局部。以上是文件和静态画面核验，**不是用户已认可两色版，也不是新一轮 Godot 实机验证**。

源目录的脚本可追溯制作过程；Aseprite 打包脚本中的家用程序路径到校后需按实际安装修改，不把家用路径当成学校环境已就绪。只看 PNG／HTML 不需要运行脚本。

## 后续怎么继续

- 先确认两色版。需要调整时只修改内部块面，继续核对 128×128 透明度，不能借调整明暗改变发梢、手脚或衣摆。
- 用户认可并要求上色后，用 **PixelLab** 做剪影内的成品绘制；提示词保持简短，说明短发、白色短袖及膝休眠服、赤脚，并写“严格保持导图外形”。只使用项目自有导图，不上传 Pixel Canals 的内容。输出仍需按认可剪影核验；轮廓漂移的结果不能直接采用。
- Aseprite 可做独立图层的局部像素精修并留修改说明。保持 Pixel Canals 的块面／像素风方向和现有像素尺度，不能自行换成写实绘制流程。
- **脸部阴影、P12／腕带、阶段二换装仍是提案，未获本轮授权，不加入。** 不把旅行装换装写成剧情定案。
- 侧面、背面和 3D 本轮都未制作。日后获授权再按同一 L2 造型制作；侧厚／正宽和背部曲线不能从正面验证记录中推定为已通过。三视图确认后再讨论分件、可换装身体、UV 和绑骨，不从被否决的旧 Tripo 白袍继续修。

## 场景与其他队列

Room 1 已冻结：墙 r24、地 r26、舱 r28、门面 r32、门灯 B、小窗暗玻璃，入口 `scenes/dev/room1_door_light_recess_b1.tscn`。本次没有改动正式角色、场景、布局、光照或 Godot 导入资源；F5 与 4F 迁移仍是后续工程任务，不能把独立美术审图当作正式集成完成。

建筑其他待定项以 [PENDING_DECISIONS.md](PENDING_DECISIONS.md) 为准：楼梯 C 旧化 v2 暂缓；FD／EL／EN、4F v6 镜头、外立面仍各有待确认内容。没有因为本轮角色工作自动选定。Demo 范围仍是走到管理设施并探索完。旧楼梯交接见[11 月 15 日已发布记录](https://github.com/Glandy-T/echoes-of-ruin/blob/ad51a8880122be896bea3f8755aaa0dc9f039b5a/docs/art/ROOM1_NEXT_SCHOOL_HANDOFF.md)，其中“主角暂停／旧白袍”为历史状态，以本交接和最新待定清单为准。

家用工作区仍有其他任务未提交的立面 GLB、Blender、`project.godot`，以及未跟踪的 credits、旧门贴图、irradiance EXR 和 `protagonist_apose_turnaround_v5/`。本次交接不包含这些工作差异，没有删除或覆盖它们。学校拉取获得的是已发布成果，不会获得这些家用本机改动。

## 给学校 Codex 的开场

> 先检查工作区并同步 GitHub main，读 `docs/art/PROTAGONIST_SCHOOL_HANDOFF_20261117.md`、`docs/art/PROTAGONIST_REDESIGN_BRIEF.md` 第4节和 `docs/art/PENDING_DECISIONS.md`。L2和 `protagonist_l2_front_silhouette_v1` 的正面剪影已经用户认可；当前 `protagonist_l2_front_twotone_v1` 是正面两色体块，尚待用户确认。先打开并排审图，不自动推进上色、侧背面或3D。外轮廓必须逐像素锁定；脸部阴影、P12／腕带和阶段二换装先不加。成品像素绘制仍按 PixelLab＋Aseprite局部精修的既有工作流。
