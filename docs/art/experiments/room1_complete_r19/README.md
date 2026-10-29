# Room 1 整室整合 r19

2026-10-30。将已确认的单项成果整合成可从标题进入的 Room 1；整室画面仍供用户最终审查。

- [实际运行截图](preview.html)
- 正式入口：`scenes/areas/military_facility/cryo_room_4f_01_3d.tscn`，F5 标题选择「はじめる」，或单独 F6。
- 技术审查：`scenes/dev/room1_complete_r19.tscn`，F6。
- 全室烘焙源：`room1_complete_r19.blend`；相对路径依赖仓库文件，下载时须保留整个仓库路径。

## 本轮变更

保持现有房间、20 舱位置／朝向、人物比例、镜头跟随方式和权限规则。20 个可见舱统一采用 v8 几何，颜色使用 r16 PixelLab 四套 A–D 外壳与共用内腔；固定分配差分，盖板与端面分别显示 01–20，P12=12。旧舱视觉与旧碰撞均禁用，不叠放两套碰撞。

墙／灯带沿用 r13，地面沿用 r15，门沿用 v7 及 r17 灯芯、r18 薄柔光。本轮没有生成或手绘新的像素做旧。脚本只导出功能编号、绑定素材并处理光照与验证；PixelLab 原始输出、请求和 Aseprite 母版仍在各素材原实验目录。

只有 P12 保持主角可交互开盖；其余 19 舱封闭。保留 P02／P12／P17 三个既有通电舱，P02／P17 红色屏幕提示；未知姓名和状态保留 `----`，没有编写新的住户信息。

## 光照与 UV

20 个位置分别烘焙闭盖受光，另有 P12 开盖、全室闭盖／P12 开盖两张墙地图，共 23 组 raw＋OIDN EXR（46 文件）。每组实际 1024 samples、关闭 adaptive sampling；舱图 1024²、墙地图 2048²。保留 raw 以便判断降噪是否掩盖错误，不以采样数本身宣告质量。

未改 UV。每舱独立图集最小非端点岛间距约 11.92px，扩边 4px；墙地图约 16.23px，扩边 6px，均为双侧扩边及双线性采样留出余量。舱图集部分岛到外边缘为 0px，**不宣称这里有 padding**；运行 shader 使用线性采样、repeat_disable／clamp，未启用光图 MIP，避免从另一边回卷采样。以后改 UV、分辨率、采样或 MIP 必须重验。

P12 与墙地随开盖进度插值两端光照，不是真实动态 GI。其余舱保持闭盖，不能把这些位置的闭盖图用于自由开盖；门与屏幕柔光仍是局部近似。全室源已删除旧 v3 舱接收体并使用新舱和当前门；外部图片采用相对路径、缺失 0。

## 验证与证据

- `source/runtime_validation.json`：355 项检查、39 次物理行走通过；20 舱布局／编号／材质／独立光图、旧碰撞禁用、侧道与中央通道、P12 占用保护及真实开关盖、门认证／穿门／复位。
- `source/title_flow.json`：新旧两套标题流程检查通过；开场对白、移动、调查、暂停、设置、返回标题及重开。正式模式隔离审查快捷键。
- `source/validation_results.json`、`upload_portability.json`：独立上传副本使用最终资产重新导入／运行的结果、实际截图哈希和 Blender 重开缺失路径检查；临时控制台日志不上传。
- `source/numbering_validation.json`：40 张编号图逐像素核对，编号区外保持 PixelLab 原图。
- `source/bake_manifest.json`、`bake_check.json`：逐图采样、扩边、哈希、输入、有限值与端点。
- `source/independent_bake_audit.json`、`independent_uv2_spacing.json`：独立读取源工程与实际 Godot UV；288 个墙地角点匹配、48 条共面共享边连续。
- `evidence/complete/`：全室六处游戏机位×开闭、四角（技术巡检真正显示前墙）、门上方、灯槽、地面、20 舱、玻璃／内部灯管、raw／降噪。
- `evidence/formal_*.png`：实际标题进入、两句开场、正常游戏和门检测过程。

截图统一由 Godot 实际输出。`pods_all_20.png` 与 `lighting_checks.png` 仅排列原帧便于核对；技术机位不保存到游戏机位。

## 操作与复现

正式模式：WASD 移动、E 调查、Enter 翻页、Esc 暂停。靠近主门自动识别芯片并开启，直接行走进入既有外部灰盒路线。

技术场景另有 O 开关 P12、V 玻璃、I raw／降噪、F4 门灯柔光、L 灯带、G 局部灯、B 屏幕、0 门前、J 舱前、H 说明。正式模式不接收这些审查键。

```text
Godot --headless --editor --path . --import --quit
Godot --headless --fixed-fps 60 --path . --scene res://scenes/dev/room1_complete_r19_verify.tscn
Godot --headless --path . --script res://scripts/dev/verify_room1_complete_title_r19.gd
Godot --headless --path . --script res://scripts/dev/verify_room1_title_flow.gd
Godot --path . --rendering-method gl_compatibility --scene res://scenes/dev/room1_complete_r19_capture.tscn
Godot --path . --rendering-method gl_compatibility --fixed-fps 60 --script res://scripts/dev/capture_room1_playable_r19.gd
```

需同时检查退出码及 `ERROR:`／`SCRIPT ERROR:`，不能只看退出码。烘焙脚本与 OIDN／路径处理脚本在 `source/`；若重烘须依次执行并重新审图。旧 128／1024 采样探针截图仅记录本轮质量排查，最终资产以 manifest 为准。

完整重烘时显式设置 `R19_REBAKE=1`、`R19_SAMPLES=1024`，清除局部选择的 `R19_ONLY`／`R19_ENDPOINTS` 环境覆盖，运行 `bake_room1_complete_r19.py`；然后运行 `bake_relative_paths_r19.py`、`bake_check_r19.py`，再做独立审计与 Godot 导入／审图。主烘焙脚本已经执行 OIDN，`bake_denoise_r19.py` 仅供从保留的 raw 单独重做降噪。不能让旧的低采样缓存被当成新的最终烘焙。

## 剩余边界

纸片主角继续临时使用，不等于完成低模 3D 主角。走廊与楼梯仍是既有灰盒／识别色，未在本轮确定其照明和正式美术。其他房间和楼层的封闭权限未扩展。本轮没有改全楼设计或新增家具。学校电脑仍须实际导入并确认运行；本机通过不能替代学校机器验收。
