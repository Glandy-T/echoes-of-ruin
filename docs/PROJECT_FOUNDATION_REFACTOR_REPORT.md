# 第一阶段正式工程整理报告

## 摘要

### 1. 本次整理是否完整完成

第一阶段计划内的工程基础整理已完成，包括目录分层、主要文件移动与重命名、引用修复、测试房间通用化、交互组件拆分，以及静态引用检查。

但由于当前学校电脑未检测到可用的 Godot 可执行文件，本次无法完成 Godot 编辑器导入、脚本解析和实际运行验证。因此，“文件整理和静态检查”已完成，“编辑器及运行时验收”仍须由用户重新打开 Godot 后按本文清单完成。

### 2. 是否成功建立外部备份或其他安全保障

- 用户已在项目文件夹之外手动建立完整本地备份，并确认备份包含 `project.godot`、所有场景、脚本、素材和 `docs` 文档。
- 当前项目内的 `.git` 是无效空目录；本次没有初始化 Git 仓库，没有创建分支或提交，没有推送远程内容，也没有修改或删除 `.git`。
- 没有删除无法确认用途的文件。
- 每组主要移动和修改后均进行了静态路径与引用检查。

### 3. 实际移动、重命名和新建了哪些主要文件

- 标题场景与脚本移入 `scenes/core/` 和 `scripts/core/`。
- 玩家场景与脚本移入 `scenes/player/` 和 `scripts/player/`。
- UI 场景和脚本重命名为 `game_ui`，并移入对应目录。
- 原 `main.tscn`、`next_room.tscn` 分别重命名为 `prototype_room_a.tscn`、`prototype_room_b.tscn`，明确归类为开发测试场景。
- 原 `main.gd` 改造为通用 `room_controller.gd`。
- 原 `next_room.gd` 改造为 `spawn_point.gd`，并保留原 UID。
- 原 `return_door.gd` 重命名并改造为通用 `scene_exit.gd`。
- 新建通用 `door.tscn`、`terminal.tscn`、`scene_exit.tscn`。
- 角色图片目录由 `assets/character/` 整理为 `assets/characters/`，文件名统一为小写。
- 新建正式区域、环境素材、UI 素材、音频和字体的预留目录。

### 4. 当前新的项目目录结构

项目现已按 `scenes`、`scripts`、`assets`、`docs` 分层。场景和脚本内部进一步分为 `core`、`player`、`ui`、`interactions`、`world`、`dev` 与 `areas`。完整真实目录树见“新目录树”章节。

### 5. 修复了哪些原有故障

- 修复 `project.godot` 主场景和 Autoload 的旧路径。
- 修复所有已移动场景、脚本、图片及导入文件中的资源路径。
- 将交互对象对玩家节点名的依赖改为 `player` 组判断。
- 将交互对象对父节点 UI 方法的依赖改为通过 `game_ui` 组查找 UI。
- 门补充实体碰撞：关闭时阻挡玩家，开启后延迟禁用碰撞。
- 门与终端状态接入 `GameState`，同一次运行中返回房间后可恢复。
- 场景出口补充目标场景存在性检查、出生点传递和可选条件限制。
- 房间出生点从固定位置改为 ID 查找，并提供缺失时的警告与回退。
- 摄像机边界从玩家场景硬编码移到房间控制器配置。
- UI 文本显示加入版本控制，避免旧计时器或淡出动画覆盖新消息。
- UI 提示改为按来源对象管理，避免重叠交互区互相错误清除提示。
- 删除 UI 默认测试文字，并明确标记尚未接线的 BGM 与语言设置。

### 6. 新建立了哪些通用系统

- **Door**：可配置状态 ID、开启位移和动画时间；支持解锁、开启、状态恢复与碰撞切换。
- **Terminal**：可配置目标门、状态 ID 和显示文本；验证目标节点与方法，避免无效目标直接导致崩溃。
- **Scene Exit**：可配置目标场景、目标出生点、进入条件和不可用提示；切换前验证资源路径。
- **Room Controller**：统一处理玩家出生点和房间摄像机边界。
- **GameState 运行时状态**：保存下一出生点和通用世界标记；当前仅在本次运行内有效。
- **Camera 边界**：由每个房间配置并应用至玩家的 `Camera2D`。
- **UI 提示与文本处理**：通过 `game_ui` 组复用；支持来源独立的提示、消息覆盖保护和淡出取消。

### 7. 哪些原有功能已经验证保留

通过代码和场景静态检查，以下功能的结构和引用已经保留：标题画面入口、开始游戏、玩家移动、跳跃、朝向、待机与行走动画、摄像机、调查提示、文本框、终端认证、门动画、房间切换、出生点、运行时场景状态、暂停菜单、设置界面入口、提示开关和返回标题。

这里的“验证保留”指静态结构、节点依赖、信号方法和资源引用检查通过，不等同于已在 Godot 中实际运行通过。

### 8. 哪些内容无法自动验证

- Godot 导入与脚本解析是否无报错。
- 关闭门的碰撞体是否在实际物理运行中正确阻挡玩家。
- 门 Tween 动画、碰撞禁用时机和返回房间后的状态恢复。
- 门、终端与出口交互范围重叠时的提示优先级和操作手感。
- 场景切换后的精确出生位置与摄像机边界体验。
- 暂停、设置、提示开关和返回标题的实际 UI 行为。
- 移动图片后 Godot 首次重新导入的结果。

### 9. 当前是否存在脚本报错、资源丢失或失效引用

静态检查没有发现已知脚本路径错误、资源丢失或失效的 `res://` 引用。所有检出的 `res://` 目标均存在，场景资源 ID、实例引用、图片引用和 UID 文件均保持一致。

但因未能启动 Godot，不能声明不存在引擎解析错误、导入错误或运行时错误。首次重新打开项目后必须检查 Godot 的 Output 与 Debugger。

### 10. 用户重新打开 Godot 后必须按顺序测试的项目

必须先等待资源重新导入，检查脚本错误，再依次验证标题、房间 A、玩家、摄像机、关闭门、终端、开门、房间 B、返回与状态恢复，最后验证暂停和重新开始重置。完整步骤与预期结果见“手动测试清单”。

### 11. 本次没有处理、留到下一阶段的内容

- 正式 4F 走廊、休眠室和一楼大厅。
- 正式调查 UI、对象名称、详细说明图片和对话期间移动锁定。
- 最终环境美术、角色美术和正式动画调整。
- BGM、音效和真实音量控制。
- 多语言系统。
- 磁盘存档。
- 战斗、敌人、物品栏和任务系统。
- 跨分辨率响应式 UI。
- 跨场景长期保留的 UI 设置。
- 后续大地图的加载与区域管理架构。

### 12. 是否建议现在开始正式整理标题画面

有条件建议。应先完成本文手动测试清单，确认 Godot 无脚本错误、资源缺失和基础流程故障；通过后可以开始整理标题画面的结构、布局与通用逻辑。现阶段不建议直接投入最终美术、多语言或音频设置，以免基础回归问题与视觉制作混在一起。

## 整理范围与安全边界

本次工作的目标是保留现有可运行原型，建立能够继续扩展的正式工程基础。没有开始制作正式 4F 走廊、休眠室或一楼大厅；没有改变世界观和剧情设定；没有删除用途不明的内容。

`WORLD_BIBLE.md` 和 `STORY_REVEAL_PLAN.md` 在本次工程整理中未被修改。`GAME_DESIGN.md` 与 `MAP_DESIGN.md` 仅进行了路径层面的必要同步，没有覆盖论文母本或新增剧情事实。

## 修改文件清单

### 新建

- `res://scenes/interactions/door.tscn`
- `res://scenes/interactions/terminal.tscn`
- `res://scenes/interactions/scene_exit.tscn`
- `res://scenes/areas/military_facility/`：空目录，正式军事设施区域预留。
- `res://assets/environments/`：空目录，环境素材预留。
- `res://assets/ui/`：空目录，UI 素材预留。
- `res://assets/audio/`：空目录，音频素材预留。
- `res://assets/fonts/`：空目录，字体素材预留。
- `res://docs/PROJECT_FOUNDATION_REFACTOR_REPORT.md`：本报告。

### 移动

- `res://title_screen.tscn` → `res://scenes/core/title_screen.tscn`
- `res://title_screen.gd` → `res://scripts/core/title_screen.gd`
- `res://title_screen.gd.uid` → `res://scripts/core/title_screen.gd.uid`
- `res://GameState.gd` → `res://scripts/core/game_state.gd`
- `res://GameState.gd.uid` → `res://scripts/core/game_state.gd.uid`
- `res://player.tscn` → `res://scenes/player/player.tscn`
- `res://player.gd` → `res://scripts/player/player.gd`
- `res://player.gd.uid` → `res://scripts/player/player.gd.uid`
- `res://door.gd` → `res://scripts/interactions/door.gd`
- `res://door.gd.uid` → `res://scripts/interactions/door.gd.uid`
- `res://terminal.gd` → `res://scripts/interactions/terminal.gd`
- `res://terminal.gd.uid` → `res://scripts/interactions/terminal.gd.uid`

### 重命名

- `res://ui.tscn` → `res://scenes/ui/game_ui.tscn`
- `res://ui.gd` → `res://scripts/ui/game_ui.gd`
- `res://ui.gd.uid` → `res://scripts/ui/game_ui.gd.uid`
- `res://main.tscn` → `res://scenes/dev/prototype_room_a.tscn`
- `res://next_room.tscn` → `res://scenes/dev/prototype_room_b.tscn`
- `res://main.gd` → `res://scripts/world/room_controller.gd`
- `res://main.gd.uid` → `res://scripts/world/room_controller.gd.uid`
- `res://next_room.gd` → `res://scripts/world/spawn_point.gd`
- `res://next_room.gd.uid` → `res://scripts/world/spawn_point.gd.uid`
- `res://return_door.gd` → `res://scripts/interactions/scene_exit.gd`
- `res://return_door.gd.uid` → `res://scripts/interactions/scene_exit.gd.uid`
- `res://assets/character/IDLE.png` → `res://assets/characters/idle.png`
- `res://assets/character/IDLE.png.import` → `res://assets/characters/idle.png.import`
- `res://assets/character/WALK.png` → `res://assets/characters/walk.png`
- `res://assets/character/WALK.png.import` → `res://assets/characters/walk.png.import`

上述“移动”和“重命名”在文件系统层面属于同一类操作；此处按主要意图区分记录。所有相应场景、脚本、导入源路径和项目设置引用均已同步修复。

### 修改

- `res://project.godot`
  - 主场景更新为 `res://scenes/core/title_screen.tscn`。
  - Autoload 更新为 `GameState="*res://scripts/core/game_state.gd"`。
- `res://scripts/core/title_screen.gd`
  - 更新开始游戏目标场景路径。
  - 开始游戏时重置演示运行时状态。
- `res://scripts/core/game_state.gd`
  - 新增 `next_spawn_id`、`world_flags`、`set_flag()`、`get_flag()` 和 `reset_demo_state()`。
- `res://scripts/player/player.gd`
  - 配合新目录和节点组结构继续使用。
- `res://scripts/ui/game_ui.gd`
  - 更新标题场景路径。
  - 加入消息版本控制和旧 Tween 清理。
  - 提示改为按来源对象管理。
- `res://scripts/interactions/door.gd`
  - 改造成通用门控制脚本，加入状态 ID、开门动画、碰撞切换和运行时恢复。
- `res://scripts/interactions/terminal.gd`
  - 改造成通用终端，加入目标验证、状态记录和 UI 组访问。
- `res://scripts/interactions/scene_exit.gd`
  - 由原返回门逻辑改造成通用场景出口，加入目标场景、出生点、条件与资源验证。
- `res://scripts/world/room_controller.gd`
  - 由原房间脚本改造成通用出生点和摄像机边界控制器。
- `res://scripts/world/spawn_point.gd`
  - 由原测试脚本改造成带 `spawn_id` 的通用出生点组件。
- `res://scenes/core/title_screen.tscn`
  - 更新脚本引用。
- `res://scenes/player/player.tscn`
  - 更新脚本和角色图片引用。
  - 玩家根节点加入 `player` 组。
  - 移除玩家场景中硬编码的房间摄像机边界。
- `res://scenes/ui/game_ui.tscn`
  - 更新脚本引用。
  - UI 根节点加入 `game_ui` 组。
  - 清除默认测试文本。
  - BGM 与语言设置明确标记为未接线。
- `res://scenes/dev/prototype_room_a.tscn`
  - 更新全部资源路径。
  - 使用通用房间控制器、Door、Terminal、Scene Exit 和出生点结构。
  - 配置 `start`、`from_room_b` 出生点。
  - A → B 的出口要求门开启状态。
- `res://scenes/dev/prototype_room_b.tscn`
  - 更新全部资源路径。
  - 使用通用房间控制器与 Scene Exit。
  - 配置 `from_room_a` 出生点和返回 A 的目标出生点。
- `res://assets/characters/idle.png.import`
  - 更新移动后的源文件路径。
- `res://assets/characters/walk.png.import`
  - 更新移动后的源文件路径。
- `res://docs/PROJECT_OVERVIEW.md`
- `res://docs/DEVELOPMENT_STATUS.md`
- `res://docs/TECHNICAL_NOTES.md`
- `res://docs/PROJECT_AUDIT_REPORT.md`
  - 同步整理后的实际路径、状态和注意事项。
- `res://docs/GAME_DESIGN.md`
- `res://docs/MAP_DESIGN.md`
  - 仅同步必要的工程路径描述，没有修改世界观或剧情结论。

### 删除

没有删除任何项目文件。

旧的空目录 `res://assets/character/` 在图片及其导入文件完整迁移后被移除；这不涉及文件内容删除。用途不明的文件均未删除。

## 新目录树

以下为第一阶段整理完成后的真实 `res://` 目录结构。空目录标注为“预留”。

```text
res://
├─ .agents/
├─ assets/
│  ├─ audio/                         （预留）
│  ├─ characters/
│  │  ├─ idle.png
│  │  ├─ idle.png.import
│  │  ├─ walk.png
│  │  └─ walk.png.import
│  ├─ environments/                  （预留）
│  ├─ fonts/                         （预留）
│  └─ ui/                            （预留）
├─ docs/
│  ├─ CHARACTER_DESIGN.md
│  ├─ DEVELOPMENT_RULES.md
│  ├─ DEVELOPMENT_STATUS.md
│  ├─ GAME_DESIGN.md
│  ├─ INTERACTION_SYSTEM.md
│  ├─ MAP_DESIGN.md
│  ├─ PROJECT_AUDIT_REPORT.md
│  ├─ PROJECT_FOUNDATION_REFACTOR_REPORT.md
│  ├─ PROJECT_OVERVIEW.md
│  ├─ STORY_REVEAL_PLAN.md
│  ├─ TECHNICAL_NOTES.md
│  └─ WORLD_BIBLE.md
├─ scenes/
│  ├─ areas/
│  │  └─ military_facility/          （预留）
│  ├─ core/
│  │  └─ title_screen.tscn
│  ├─ dev/
│  │  ├─ prototype_room_a.tscn
│  │  └─ prototype_room_b.tscn
│  ├─ interactions/
│  │  ├─ door.tscn
│  │  ├─ scene_exit.tscn
│  │  └─ terminal.tscn
│  ├─ player/
│  │  └─ player.tscn
│  └─ ui/
│     └─ game_ui.tscn
├─ scripts/
│  ├─ core/
│  │  ├─ game_state.gd
│  │  ├─ game_state.gd.uid
│  │  ├─ title_screen.gd
│  │  └─ title_screen.gd.uid
│  ├─ interactions/
│  │  ├─ door.gd
│  │  ├─ door.gd.uid
│  │  ├─ scene_exit.gd
│  │  ├─ scene_exit.gd.uid
│  │  ├─ terminal.gd
│  │  └─ terminal.gd.uid
│  ├─ player/
│  │  ├─ player.gd
│  │  └─ player.gd.uid
│  ├─ ui/
│  │  ├─ game_ui.gd
│  │  └─ game_ui.gd.uid
│  └─ world/
│     ├─ room_controller.gd
│     ├─ room_controller.gd.uid
│     ├─ spawn_point.gd
│     └─ spawn_point.gd.uid
├─ .editorconfig
├─ .gitattributes
├─ .gitignore
├─ icon.svg
├─ icon.svg.import
├─ project.godot
└─ README.md
```

`.git/` 为用户说明的空目录，未被修改；因其不是 `res://` 项目资源，未列入上述资源树。

## 场景与脚本对应表

| 场景或组件 | 对应脚本 | 用途 | 分类 |
|---|---|---|---|
| `res://scenes/core/title_screen.tscn` | `res://scripts/core/title_screen.gd` | 项目主入口；开始游戏、进入设置/说明并退出 | 正式基础场景 |
| `res://scenes/player/player.tscn` | `res://scripts/player/player.gd` | 玩家移动、跳跃、朝向、动画和摄像机承载 | 正式基础场景 |
| `res://scenes/ui/game_ui.tscn` | `res://scripts/ui/game_ui.gd` | 调查提示、文本消息、暂停菜单、设置入口和返回标题 | 正式基础场景 |
| `res://scenes/interactions/door.tscn` | `res://scripts/interactions/door.gd` | 可解锁、开启动画、实体阻挡及运行时状态恢复 | 通用组件 |
| `res://scenes/interactions/terminal.tscn` | `res://scripts/interactions/terminal.gd` | 玩家认证交互、门控制、状态记录与反馈文本 | 通用组件 |
| `res://scenes/interactions/scene_exit.tscn` | `res://scripts/interactions/scene_exit.gd` | 条件式场景切换和目标出生点传递 | 通用组件 |
| `res://scenes/dev/prototype_room_a.tscn` | `res://scripts/world/room_controller.gd` | 验证玩家、UI、终端、门、出口、状态和出生点的主要原型房间 | 开发测试场景 |
| `res://scenes/dev/prototype_room_b.tscn` | `res://scripts/world/room_controller.gd` | 验证双向场景切换、返回出生点和运行时状态恢复 | 开发测试场景 |
| 房间内 `Marker2D` 出生点节点 | `res://scripts/world/spawn_point.gd` | 以 `spawn_id` 注册并标识出生位置 | 通用组件 |
| `res://scenes/areas/military_facility/` | 暂无 | 正式军事设施场景目录 | 尚未使用的预留目录 |

## 主要系统与代码修改

### GameState 运行时状态

`res://scripts/core/game_state.gd` 作为 Autoload 保存：

- `next_spawn_id: StringName = &"start"`：下一个场景应使用的出生点 ID。
- `world_flags: Dictionary = {}`：同一次游戏运行期间的通用状态字典。
- `set_flag(id, value)`：写入状态。
- `get_flag(id, default_value = false)`：读取状态并支持默认值。
- `reset_demo_state()`：开始新一轮原型流程时清空状态并重置出生点。

这些状态只存在于内存中。关闭游戏、停止运行或重新启动项目后不会保留，当前并不是磁盘存档系统。

### Door

`res://scenes/interactions/door.tscn` 包含门洞、门板和带 `CollisionShape2D` 的静态碰撞体。`door.gd` 提供：

- 可导出的 `state_id`。
- 默认向上移动的 `open_offset = Vector2(0, -180)`。
- 默认 `animation_time = 1.0`。
- `unlock()`、`open()`、`unlock_and_open()` 公共方法。
- 门关闭时保持碰撞，开启后以延迟方式禁用碰撞。
- 从 `GameState` 恢复时直接设置开启位置并禁用碰撞，不重复播放 Tween。

### Terminal

`terminal.gd` 提供可配置的目标门路径、状态 ID、提示文字、激活文字、已使用文字和失败文字。终端会检查目标节点是否存在以及是否提供 `unlock_and_open()`，无效配置时给出警告，避免因直接调用不存在的方法而崩溃。

脚本中没有写入正式剧情内容；原型专用文本配置在开发测试场景中。

### Scene Exit

`scene_exit.gd` 替代原先仅服务于返回门的脚本，提供：

- `target_scene_path`：目标场景。
- `target_spawn_id`：目标出生点。
- `prompt_text`：交互提示。
- `required_flag_id` 与 `required_flag_value`：可选进入条件。
- `unavailable_text`：条件不满足时的反馈。
- 使用 `ResourceLoader.exists()` 验证目标资源。
- 切换前写入 `GameState.next_spawn_id`。

当前原型 A → B 要求门开启状态；B → A 不要求额外状态。

### Room Controller 与出生点

两个原型房间共用 `room_controller.gd`。控制器查找 `player` 组中的玩家，按 `GameState.next_spawn_id` 查找出生点，并在目标缺失时警告和回退到默认出生点；若默认出生点也缺失，则保留玩家在场景中的原始位置。

`spawn_point.gd` 继承 `Marker2D`，导出 `spawn_id`，并加入 `spawn_point` 组。当前出生点为：

- 房间 A：`start`、`from_room_b`。
- 房间 B：`from_room_a`。
- A → B：使用 `from_room_a`。
- B → A：使用 `from_room_b`。

### 摄像机边界

原本写死在玩家场景中的边界已移除。每个房间通过 `room_controller.gd` 配置并应用至 `Player/Camera2D`。两个原型房间当前配置为：

- Left：`0`
- Top：`0`
- Right：`1797`
- Bottom：`650`

该数值用于维持原型现有可视范围；正式房间应按实际场景尺寸单独配置。

### UI 提示与文本处理

- `GameUI` 根节点加入 `game_ui` 组，交互对象不再假设 UI 一定位于其父节点。
- `show_text()` 使用消息版本机制；新消息出现时会使旧计时器失效并终止旧淡出 Tween，避免旧回调隐藏新消息。
- 提示以来源节点为键保存；一个交互区域退出时只移除自己的提示，不会清除仍处于范围内的另一个对象提示。
- 默认 `TextLabel` 测试文字已清空。
- 设置界面中的 BGM 与 Language 标记为“未接続”，对应回调仍为占位输出，避免误认为功能已经完成。

当前 UI 仍由每个房间分别实例化，设置状态会在场景切换时重置。UI 也仍使用固定像素布局，尚未完成响应式适配。

## 当前原型流程

1. 项目从 `res://scenes/core/title_screen.tscn` 启动。
2. 选择 START 后调用 `GameState.reset_demo_state()`，进入 `prototype_room_a.tscn`。
3. 玩家在房间 A 接近终端并交互，终端记录认证状态并调用 Door。
4. Door 播放向上开启动画，记录开启状态并禁用碰撞。
5. 玩家通过 Scene Exit 进入房间 B，出生于 `from_room_a`。
6. 玩家从房间 B 返回房间 A，出生于 `from_room_b`。
7. 同一次运行中，门保持开启，终端显示已认证状态。
8. 返回标题后再次 START，会重置演示状态，门和终端恢复初始状态。

## 引用检查

### 检查结果

- [x] **`project.godot` 主场景**：已检查，指向 `res://scenes/core/title_screen.tscn`，目标存在。
- [x] **Autoload 路径**：已检查，`GameState` 指向 `res://scripts/core/game_state.gd`，目标存在。
- [x] **`change_scene_to_file` 路径**：已搜索并检查标题、UI 返回标题和通用 Scene Exit 的相关调用；固定路径目标存在，Scene Exit 的运行时目标另有资源存在性验证。
- [x] **`preload` / `load` 路径**：已全局搜索；当前脚本中没有需要修复的相关旧路径引用。
- [x] **`.tscn` 资源引用**：已检查所有场景的脚本、图片、子资源和外部资源引用，未发现指向旧目录的路径。
- [x] **场景实例引用**：已检查玩家、UI、Door、Terminal 与 Scene Exit 的场景实例路径，目标均存在。
- [x] **SpriteFrames 与图片引用**：已检查玩家 SpriteFrames 对 `idle.png`、`walk.png` 的引用，以及图片导入源路径。
- [x] **UID 相关文件**：9 个 `.gd.uid` 均已保留并随脚本移动，UID 唯一；没有发现重复 UID 或丢失的脚本 UID 文件。

### 其他静态检查

- 所有检出的 `res://` 路径均能对应到现有文件。
- 未发现仍指向旧 `res://Main`、`res://TitleScreen`、根目录 `main`、`next_room`、`player`、`ui` 或 `GameState` 路径的当前源码引用。
- `.tscn` 的 `ExtResource`、`SubResource` 与父节点路径在文本结构上保持一致。
- Terminal 与 Scene Exit 的信号回调方法存在。
- `GameUI`、Door 和 GameState 所需公共方法存在。
- 场景 `load_steps` 与资源计数完成静态核对。
- 项目根目录不再残留旧版 `.gd`、`.gd.uid`、`.tscn` 或角色 `.png` 文件。
- `res://scenes/areas/military_facility/` 当前为空，没有误创建正式地图内容。
- `.git` 目录仍为空且未被修改。

### UID 保留情况

以下脚本 UID 文件被保留并随脚本移动：

- `res://scripts/player/player.gd.uid`
- `res://scripts/ui/game_ui.gd.uid`
- `res://scripts/interactions/door.gd.uid`
- `res://scripts/core/game_state.gd.uid`
- `res://scripts/world/spawn_point.gd.uid`
- `res://scripts/world/room_controller.gd.uid`
- `res://scripts/interactions/scene_exit.gd.uid`
- `res://scripts/interactions/terminal.gd.uid`
- `res://scripts/core/title_screen.gd.uid`

没有主动重建或更换这些 UID，以降低场景脚本引用失效的风险。

## 验证结果与限制

### 已完成的静态验证

- 文件存在性检查通过。
- 旧路径残留搜索通过。
- 场景外部资源和实例引用检查通过。
- 项目主场景与 Autoload 路径检查通过。
- 图片导入源路径检查通过。
- 脚本 UID 保留和唯一性检查通过。
- 关键公共方法与信号处理方法检查通过。
- 世界观与核心剧情文档未被本次工程整理修改。

### 无法完成的自动验证

当前系统 PATH、常见安装位置和快捷方式中没有发现 Godot 可执行文件，因此没有执行：

- Godot 命令行 `--headless` 导入。
- GDScript 实际解析。
- 场景实际加载。
- 游戏运行回归测试。
- 物理碰撞、Tween、信号与输入的运行时测试。

首次在 Godot 中打开项目时，移动后的角色图片可能触发重新导入或缓存更新，这是正常预期，但必须确认没有导入失败。

## 警告与剩余风险

1. **尚未运行 Godot 验证**：静态检查通过不代表运行时必然无误，Godot Output 和 Debugger 是下一步的强制检查项。
2. **碰撞手感需实机确认**：Door 的关闭碰撞、开启后禁用时机及玩家穿过门洞的实际效果需运行验证。
3. **交互范围可能重叠**：Door、Terminal 和 Scene Exit 在原型房间内距离较近，需要确认提示优先级与按键响应没有造成误操作。
4. **运行时状态不是存档**：`GameState.world_flags` 只在当前运行中存在，关闭游戏后全部丢失。
5. **UI 仍按房间实例化**：切换场景后设置项会重置；未来若要求跨房间保持，应再决定使用持久 UI、Autoload 设置或正式存档。
6. **UI 使用固定像素布局**：不同窗口尺寸可能出现位置或缩放问题。
7. **Scene Exit 使用资源路径字符串**：通用化后仍依赖场景中正确填写目标路径；脚本会验证目标存在，但无法自动判断设计意图是否正确。
8. **房间摄像机边界需逐房配置**：新增房间若沿用默认值，可能与真实地图大小不符。
9. **正式区域目录目前为空**：本次没有开始正式 4F 走廊、休眠室或一楼大厅，符合安全边界。
10. **文件移动后的编辑器缓存**：Godot 首次打开可能需要重新扫描资源；在确认导入完成前不要根据短暂警告继续批量移动文件。

## 手动测试清单

请按顺序逐项测试。若某一步失败，应先停止后续正式制作，记录 Output/Debugger 的完整错误和触发步骤。

- [ ] **1. 打开项目并等待导入完成**
  - 操作：使用 Godot 4.6 打开项目，等待右下角导入任务结束。
  - 正确结果：项目文件系统完整显示；`idle.png` 与 `walk.png` 可正常预览；没有持续导入失败提示。

- [ ] **2. 检查脚本解析与 Debugger**
  - 操作：查看 Script 面板、Output 和 Debugger。
  - 正确结果：没有 GDScript 解析错误，没有脚本丢失或 UID 无法解析错误。

- [ ] **3. 运行项目并确认标题画面**
  - 操作：按 F6/F5 中适用的项目运行方式启动主场景。
  - 正确结果：显示标题画面；主场景不是测试房间或空白画面；按钮可以响应。

- [ ] **4. 从标题选择 START**
  - 操作：点击 START。
  - 正确结果：进入 `prototype_room_a.tscn`，玩家出现在 `start` 出生点；没有无效场景路径错误。

- [ ] **5. 测试玩家移动与跳跃**
  - 操作：左右移动、停止、跳跃，并观察两个方向。
  - 正确结果：玩家可移动和跳跃；停止时显示待机动画，移动时显示行走动画；朝向随方向翻转。

- [ ] **6. 测试摄像机边界**
  - 操作：移动到房间左右端并跳跃接近上下边界。
  - 正确结果：摄像机跟随玩家且不明显越出房间配置范围；没有找不到 `Camera2D` 的警告。

- [ ] **7. 确认关闭的门具有实体阻挡**
  - 操作：未使用终端前尝试穿过 Door。
  - 正确结果：门板关闭，玩家无法穿过门的碰撞区域。

- [ ] **8. 测试锁定状态反馈**
  - 操作：在未认证时接近门或出口并按交互键 `E`。
  - 正确结果：UI 显示对应锁定或不可用文本；不会切换场景，也不会出现脚本错误。

- [ ] **9. 使用 Terminal 认证**
  - 操作：进入终端范围，确认提示后按 `E`。
  - 正确结果：显示认证反馈；Door 向上播放一次开启动画；Output 中没有目标门无效或方法缺失警告。

- [ ] **10. 确认开门后可以通过**
  - 操作：门动画完成后穿过原碰撞区域。
  - 正确结果：玩家可以正常通过；门不会反复播放开启动画或继续阻挡。

- [ ] **11. 从房间 A 进入房间 B**
  - 操作：进入 A 房间出口范围并按 `E`。
  - 正确结果：加载 `prototype_room_b.tscn`；玩家出现在 `from_room_a` 出生点；UI 正常存在。

- [ ] **12. 从房间 B 返回房间 A**
  - 操作：使用 B 房间的返回出口。
  - 正确结果：返回 `prototype_room_a.tscn`；玩家出现在 `from_room_b`，而不是默认 `start`。

- [ ] **13. 验证同次运行的状态恢复**
  - 操作：返回房间 A 后观察 Door，再次使用 Terminal。
  - 正确结果：Door 保持开启且碰撞关闭；Terminal 显示已认证/已使用反馈，不重新执行完整开门流程。

- [ ] **14. 测试暂停菜单和设置界面**
  - 操作：打开暂停菜单，切换提示设置，进入设置页并返回，再恢复游戏。
  - 正确结果：暂停与恢复正常；界面可进入和返回；BGM、Language 显示未接线，不应误表现为已有功能。

- [ ] **15. 测试返回标题**
  - 操作：从游戏 UI 选择 TITLE。
  - 正确结果：返回 `title_screen.tscn`；没有旧根目录路径或场景不存在错误。

- [ ] **16. 测试重新开始时重置状态**
  - 操作：回到标题后再次点击 START。
  - 正确结果：进入房间 A 的 `start` 出生点；Door 恢复关闭并重新阻挡；Terminal 恢复未认证状态。

- [ ] **17. 全流程检查 Output 与 Debugger**
  - 操作：完成上述流程后查看 Output 和 Debugger。
  - 正确结果：没有 invalid path、missing node、missing method、invalid resource、信号调用或类型错误。

- [ ] **18. 测试重叠提示处理**
  - 操作：在 Door、Terminal、Scene Exit 的交互范围边缘来回移动，使多个范围先后进入和退出。
  - 正确结果：当前可交互对象的提示保持合理；离开一个范围不会错误清除仍在另一个范围内的提示。

## 下一阶段建议顺序

1. 先完成全部手动回归测试，并保存所有异常的截图、Output 和复现步骤。
2. 若存在脚本或引用错误，只修复第一阶段基础设施，不同时进行标题美术改造。
3. 基础流程全部通过后，整理标题画面的节点结构、布局和通用按钮行为。
4. 再决定 UI 跨场景复用、设置持久化和响应式布局方案。
5. 确认正式场景规范后，才开始创建军事设施区域的正式建筑场景。
6. 正式建筑制作期间逐房配置出生点、摄像机边界和出口目标，并持续执行静态引用检查与运行回归。

## 本阶段结论

第一阶段已把原先集中在项目根目录、测试用途不清和节点依赖较强的原型，整理为具有明确层级的 Godot 工程基础。核心原型内容没有被删除，测试房间被明确标记为开发场景，门、终端、出口、出生点、房间控制器、运行时状态和 UI 访问方式已具备复用结构。

当前最重要的下一步不是继续扩大地图，而是在 Godot 4.6 中完成本文手动测试。只有确认导入、脚本解析、碰撞、场景切换和状态恢复全部通过后，才建议进入标题画面整理或正式建筑制作。
