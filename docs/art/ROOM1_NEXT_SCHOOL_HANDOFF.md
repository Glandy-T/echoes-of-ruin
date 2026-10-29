# Room 1 学校交接：整室整合 r19

更新：2026-10-30。本文替代此前“只有 P12 是新舱／F5 未切换／门待实现”的交接状态；历史过程查看 Git 历史。

## 学校先做

1. 在干净工作副本拉取 GitHub `main`。有学校自己的修改时先保留并核对，避免直接覆盖；家里旧 HEAD 的主目录不要强制 reset。
2. 用 Godot 4.6.2 打开根目录 `project.godot`，等待导入完成，F5 →「はじめる」。正式目标为 `scenes/areas/military_facility/cryo_room_4f_01_3d.tscn`。
3. 看开场两句对白、走出 P12、检查全室编号、移动／遮挡、E 调查、暂停／返回标题；靠近主门自动认证，穿门进入既有走廊灰盒。学校机器仍需亲自确认，本机检查不是学校验收。

操作：WASD、E、Enter、Esc。正式模式不会响应调材质／开盖／灯效的审查键。

## 当前已经整合

- 全室 20 舱统一 v8，位置与朝向不变；四套 r16 PixelLab 外壳差分固定分配，盖板及端面分别显示 01–20。仅 P12 可交互开盖；其余舱封闭。未知姓名／状态不编造。
- r13 四墙／灯带、r15 地面、v7 主门、r17 内侧窄灯芯与 r18 薄光晕。门板遮住的灯面不会隔门发亮。
- 每舱按实际位置烘焙，不复制 P12 光图。23 组 raw＋OIDN 图均实际 1024 samples；pod 4px／shell 6px 扩边。P12 开闭和墙地使用端点插值，不是真动态 GI。
- 保留原开场、移动、调查、暂停、设置和外部灰盒路线；主角仍为旧 2D 精灵的 Sprite3D 临时方案。
- 本轮复用已确认 PixelLab 颜色图，只新增功能编号与光照整合。没有重新画污斑，没有把新旧做旧图叠加。

## 核验与查看

- [整室实际截图](experiments/room1_complete_r19/preview.html)／[技术说明](experiments/room1_complete_r19/README.md)。
- 本机运行检查：355 项、39 次物理行走；20 舱编号／材质／独立受光、旧碰撞禁用、侧道与主通道、P12 占用保护、自动门认证／穿门／复位。
- 新旧标题流程均通过，含重开／暂停设置及正式模式快捷键隔离；检查 Godot 退出码及错误输出，未以退出码单独判断。
- 独立 UV／EXR 核验：288 个墙地角点匹配、48 条共面共享边连续；23 组光图哈希与 manifest 一致。四角、前墙、门上方、灯槽、地面、20 舱和玻璃已安排实际截图。

技术审查可 F6 `scenes/dev/room1_complete_r19.tscn`：O 开关 P12、V 玻璃、I raw／降噪、F4 门光晕、0 门前、J 舱前。技术相机不替换游戏相机。

## 制作文件

- 全室 Blender：`docs/art/experiments/room1_complete_r19/room1_complete_r19.blend`，需与仓库相对路径贴图一起保留。
- 动画单舱：`docs/art/experiments/room1_pod_standard_v8/`；材质母版 `room1_pod_pixellab_r16/editable/`。
- 墙／灯母版：`room1_wall_lamp_r13/editable/`；地面母版：`room1_floor_variants_r15/editable/`（均在 `docs/art/experiments/` 下）。
- 当前运行包：`assets/art/room1_complete_r19/`。更多入口见 [素材目录](素材目录.md)。

旧编号资源仍有继承依赖，不直接删除。历史已归档内容见根目录 [从这里开始](../../从这里开始.md)。账户配置、缓存和临时日志不作为交付资产。

## 下一阶段

先由用户审查整室实际画面，再推进走廊／楼梯正式美术与照明；目前外部路线仍是灰盒识别色，不能视作最终效果。低模 3D＋像素贴图主角另开制作范围，临时纸片不继续投入大量精修。

继续使用 GitHub main 最新设计和冻结 CAD 的空间关系；其他房间、其他楼层的芯片权限及四区分隔不擅自改动。像素贴图生成／返修始终走 [PixelLab 工作流](PIXEL_TEXTURE_WORKFLOW.md)，Pixel Canals 为风格硬参考，其 NoAI 参考图不上传生成服务。
