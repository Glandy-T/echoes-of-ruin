# Room 1 Godot 导入与搭建 r1 — 2026-10-14

本轮在学校电脑用项目目录内 Godot 4.6.2 实际导入、搭建并渲染。用户已指出墙地 r1 太干净、看不出时间痕迹，**墙地 r1 暂不通过**；今天保留现有贴图做导入、布局、镜头与灯光验证，材质返修留到方便的电脑上。

## 直接查看

打开仓库根 `project.godot`，打开 `scenes/dev/room1_import_review_r1.tscn`，按 F6 运行当前场景。F5 仍运行原游戏入口。

运行窗口快捷键：

| 按键 | 操作 |
|---|---|
| 1 | 全室低角度正交总览 |
| 2 | 后排 P12 单舱斜角近景，能看见脚端屏幕 |
| 3 | 门与后墙近景 |
| F | 切换剖切／完整房壳；完整房壳会遮挡室内，这是正常结果 |
| L | 切换本轮审图灯光，保留环境基础光与贴图自发光 |
| O | P12 关闭／45°打开的静态 GLB 替换，非连续动画 |

## 场景组织

- `Shell`：完整房壳 GLB。默认仅在本审图场景隐藏前墙、左墙、屋顶，原 GLB 不变。
- `Pods`：20个关闭态 v3 贴图舱，按已有 `pod_placement_godot.json` 的米制坐标与旋转放置。没有叠加 layout-review 的灰模舱。
- `ReviewCamera`：三个检查镜头；保留项目原窗口与 Viewport 设置。
- `WorldEnvironment`：基础环境光与深灰背景。
- `ReviewLights`：淡灰蓝灯带附近8个低强度点光代理，加一盏带阴影的检查用方向光。只是可读性试排，不是最终应急照明或真实连续灯带投光。

全项目只增加 `filesystem/import/blender/enabled=false`，避免本地旧工作目录中的 `.blend` 素材触发学校电脑的 Blender 路径要求。游戏使用已有嵌入纹理的 GLB；母版文件仍保留。依据 [Godot 4.6 ProjectSettings](https://docs.godotengine.org/en/4.6/classes/class_projectsettings.html#class-projectsettings-property-filesystem-import-blender-enabled)。

未改变主场景、Viewport、正式 Camera、移动方式或游戏玩法。没有增加角色、碰撞、导航、门禁、动态屏幕或连续动画。没有新增 PixelLab 用量或修改 GLB、像素贴图。

## 实际验证

`validation.json` 记录四份 GLB 的实例化、纹理采样和UV0读回，以及20舱数量、清单位置／朝向、剖切／完整切换和静态姿态切换检查。实际渲染使用 GL Compatibility / OpenGL 3.3，学校电脑 GPU 为 GTX 1080。

本目录五张 PNG 来自实际 Godot 1280×720 窗口：总览、关闭单舱、静态打开单舱、门墙、关灯对比。已逐张目视查看；贴图能读出，门、舱、地面均可见，脚端屏幕近景可辨。最近邻材质读回全部为0。

待继续：墙地时间痕迹返修；最终灯光与受控色阶 Shader；真实使用镜头下的像素密度与细节；各舱编号仍复制01，前排朝向的端面编号还可见倒向／镜像，需后续逐面UV与标识设计检查。此次文件导入通过不等于美术或玩法验收。

## 复现

在仓库根，用 Godot 4.6.2 可执行文件运行：

```powershell
& '<Godot控制台exe>' --headless --path . --editor --import
& '<Godot控制台exe>' --headless --path . --script res://scripts/dev/build_room1_import_review.gd
& '<Godot控制台exe>' --path . --script res://scripts/dev/validate_room1_import_review.gd --resolution 1280x720 --quit-after 240
```

生成脚本会重建本场景，手工编辑后不要直接重跑覆盖；先另存版本。验证脚本也可用 `--headless` 做资源与搭建检查，但无图形窗口时不导出截图。
