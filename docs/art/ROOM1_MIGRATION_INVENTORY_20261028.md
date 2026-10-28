# Room 1 旧功能核对（2026-10-28）

当前工作副本 HEAD 为 bbc37ff，GitHub main / 本地 origin/main 缓存为 d2afca7；工作副本包含原有修改和未跟踪资源，未重置或同步。此记录基于本机文件，学校电脑仍需自行导入、试玩和目视审查。

## 旧版已有功能与迁移边界

| 功能 | 旧版实际入口 | 新审查场景状态及迁移注意 |
|---|---|---|
| 移动、跳跃、朝向 | `scenes/player/player.tscn`、`scripts/player/player.gd` | 新场景为 3D 平面移动及纸片 idle/walk，碰撞和尺度不同；旧版跳跃未迁移，是否需要需结合新玩法判断。 |
| 调查、对话与特写 | `scenes/interactions/investigation_point.tscn`、`scenes/ui/game_ui.tscn` | 新场景尚未接入。旧交互依赖 Area2D、Node2D 屏幕坐标和 player 组；需重新适配 3D 检测和屏幕投影，UI 对话时需要锁定新角色移动。 |
| 认证终端与开门 | `scenes/interactions/terminal.tscn`、`door.tscn` | 旧方案按 E 操作终端，记录 `cryo_room_exit_authorized` 并打开 2D 门；新方向是人员芯片自动检测，不能原样迁移终端或把旧认证规则当作定案。 |
| 运行时状态、出生点 | `scripts/core/game_state.gd`、`scripts/world/room_controller.gd` | GameState 为 autoload，状态仅在本次运行中保存。旧出生点和镜头控制依赖 2D，新场景需独立适配。 |
| 退出、暂停、设置 | `scripts/interactions/scene_exit.gd`、`scripts/ui/game_ui.gd`、`scripts/core/title_screen.gd` | 旧房间的出口路线目前是禁用锚点，不代表已有通往下一场景的完成流程；音量和语言设置是占位。新审查场景未接入游戏 UI。 |

旧房间包含舱体、巡查表、故障便条、同意书、废弃物回收口等调查文本；这些随旧空间设计配置，不代表这些物件或叙事细节已批准放入新房间。

## 本机验证

Godot 4.6.2 完成项目导入；两个场景均以 headless 启动并正常退出。运行 `Godot_v4.6.2-stable_win64_console.exe --headless --path <项目目录> --script res://scripts/dev/verify_room1_handoff_20261028.gd`：旧终端直接调用激活后，门开启、运行时状态写入，对话打开时锁定角色、关闭后解锁；新场景模拟移动后切换 walk、停止后恢复 idle，灯带开关传入角色材质。此为程序核验，未验证真实按键接近、画面遮挡、学校机器或完整游玩流程。

## 下一步

1. 在实际画面中检查新角色比例、遮挡及光照，并在学校机器复验导入。
2. 优先设计 3D 交互与对话输入锁定的适配，在独立审查场景验证；不改变正式主入口。
3. 检查现有门模型、方向和碰撞，制作芯片自动检测的独立试验。门外观和认证规则仍待确认，不增加壁面面板。
4. 按已确认的空间和叙事逐项决定调查内容，避免复制旧灰盒设施。20舱推广与全室 GI 单独安排。

