# Room 1 学校交接：纸片主角与旧功能迁移

> 2026-10-29柔光补充：最新候选为 `scenes/dev/room1_door_soft_glow_r18.tscn`（F6，F4比较有无柔光），[对照图](experiments/room1_door_soft_glow_r18/preview.html)。r17灯芯和颜色获初步认可，本轮只给露出的灯面加薄光晕，保留r17作为无柔光基准；关闭无残光，半开被挡右侧不亮，人物遮挡与六处游戏机位检查通过。未改像素贴图、UV、烘焙、门碰撞／认证或F5入口，r18待审。

> 2026-10-29门灯补充：最新候选运行 `scenes/dev/room1_door_inner_light_r17.tscn`（F6，F4比较），[门内侧灯对照](experiments/room1_door_inner_light_r17/preview.html)。普通前门框不再变绿；参考实物门沿灯的暗色型材＋窄LED芯，只亮已露出的内侧，半开时右侧不穿透。宽薄荷绿中间候选已否定。真实认证、开门、穿门、关门及截图遮挡检查通过；仍待用户审图，没有改动PixelLab颜色图、原认证小窗、门运动／碰撞或F5入口。继承下述r16／r15／r13材料。

> 2026-10-29材质补充：当前单舱候选为`scenes/dev/room1_pod_pixellab_r16.tscn`（F6；P旧新、K差分、O开盖），[开闭与材质对比](experiments/room1_pod_pixellab_r16/preview.html)。使用r15地坪、r13墙／灯带，仅替换P12的实体颜色图；四套外壳、Aseprite和打包Blender源已上传。几何／UV／动画／玻璃／屏幕／灯管保持；单舱材质已获初步认可；其他19舱仍旧，推广时按现有P01–P20分别显示01–20（P12=12），盖板／端面一致且编号独立于A–D差分。帮助器已要求显式传入实例编号，并通过4×20测试；再按位置处理光照，不能复制P12专用光照。下文保留早期功能交接，旧r9地面及v4旧化不是最新材质候选。

学校电脑先更新或克隆 GitHub main，然后打开 `project.godot`。家里这份工作目录的 Git HEAD 仍是旧版，且 `project.godot` 有原有本地修改，大量当前资产在此旧 HEAD 下显示未跟踪；不要直接强行重置或覆盖，先备份并核对后再同步。用 F6 运行 `scenes/dev/room1_sprite_player_lighting_r2.tscn`；这是新的当前审查入口，不是主场景。原2D游戏入口仍在 `scenes/player/player.tscn` 及原有场景中，先运行并核对旧行为，再按实际需求迁移。

## 已完成

- 旧版 `assets/characters/idle.png` / `walk.png` 的原帧以 Sprite3D 方式面向镜头；最近邻采样、内容高度1.65m，原画纵横比例保持，脚底对应原3D碰撞脚点。使用既有3D角色移动与碰撞，横向移动翻转、移动时播放walk，静止播放idle。旧2D功能并未整套迁移。
- P12 是统一 v8 舱，真实约2秒先抬再侧滑，盖体碰撞跟随、占用保护、双侧灯管与独立屏幕可用；屏幕现为用户确认的窄边方案。其他19个舱仍是旧版，不误认已完成全室升级。
- [角色截图和验证](experiments/room1_sprite_player_review_r1/README.md)、[舱体接口和局限](experiments/room1_pod_standard_v8/README.md)、[屏幕对照](experiments/room1_pod_screen_v8_1/preview.html)。P12两端受光针对该位置，中途为插值，周边仍为原房间GI。地面r9仍为搁置待审方案。

## 接下来在学校做

1. 在学校机器先确认项目导入、审查场景、角色比例、移动和遮挡，再对照旧2D版本列出实际已有功能与入口。逐项迁移必要交互、状态与流程，验证后再决定是否替换正式主场景；不要假定2D脚本可直接挂到3D节点。
2. 处理当前主门的动画与触发：先读 [2026-10-29 一体化认证门／黄绿红灯语 Brief](ROOM1_INTEGRATED_DOOR_ACCESS_BRIEF.md)，沿已讨论的人员芯片自动检测、单人通行持续监测、门框内侧绿灯及越权/尾随红灯方向制作；先检查现有门模型、横向滑移方向与碰撞。具体尺寸、亮度、安全防夹等未决，避免擅自增加墙面认证面板或把历史临时扫描线定稿。
3. 整室推广新舱、编号/屏幕状态、差异化贴图与全室GI需另外安排；不要将单舱验证写成全室完成。

## 素材和整理

[项目根目录入口](../../从这里开始.md)列出了当前模型、分层像素母版和运行入口。旧编号的墙地运行文件部分被继承链直接使用，不能按编号删除；舱体可编辑像素源仍在 `room1_pod_volume_v4/editable/`，四墙在 `room1_seam_contact_r6/editable/`，当前地坪在 `room1_floor_palette_r9/editable/`。历史实验可从 GitHub 恢复。本地尚未经核验／需补存的旧材料继续保留，不能把整理清单视为全盘清空。

本机整理结果：53个历史实验／角色试作目录已在逐文件核对GitHub后清理，约506 MiB；具体清单见 [整理记录](cleanup_room1_result.json)。历史源可在 GitHub 原路径或 `docs/art/archive_local_20261028/` 查找，归档两份 MANIFEST 按原路径和 SHA256 列出补存文件。API连接检查目录因可能包含账户信息仍留本机，未上传；原始缓存与日志没有作为作品归档。当前所需的旧编号基础文件和像素母版继续保留。

整理后重新运行纸片角色审查入口，实测角色行走约1.65m时使用walk帧，停止后回到idle，Godot错误输出为空；这是当前机器的运行验证，学校电脑仍需重新导入和确认。

## 纸片主角受光修正 r2

原 `Sprite3D` 默认不受光，导致角色接近原图亮度。现在优先运行 `scenes/dev/room1_sprite_player_lighting_r2.tscn`：原像素图、比例、动画和碰撞保持，主角按房间灯带位置、灯带开关和自身位置接受动态近似照明。L可检查灯带开关，开灯与关灯见[对照](experiments/room1_sprite_player_lighting_r2/preview.html)。这是为移动2D精灵补充的灯带近似，不是真实动态GI或遮挡计算；未来迁移功能时需按场景光照方案继续验证。
