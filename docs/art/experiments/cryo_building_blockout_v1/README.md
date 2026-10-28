# 单栋休眠楼空间骨架 v1

这是整栋楼的首轮空间低模，用于检查体量和标准层关系，**不是最终外立面或可玩游戏场景**。

- [Blender 可编辑工程](cryo_building_blockout_v1.blend) · [三张视图](preview.html) · [本轮开工简报](../../CRYO_BUILDING_LOWPOLY_BRIEF.md)
- 地上 1F–16F、地下 B1–B4，标准层从冻结的平面坐标重建为独立低模模板，20层以集合实例复用。每层标记48个房间，其他休眠室只保留墙和封闭门面，不制作舱体或室内。
- 4F 的 SW-01 是**暂定**主角房位置，黄色仅为位置提示；此房尚未接入现有 Godot Room 1。它的门面对象可隐藏，以露出 D001 人员门洞。
- `UNDERGROUND_B1_B4__HIDEABLE` 集合可单独隐藏；各层分别有集合。中央机器核心和交通核是不可进入的简化体块。门面目前只表示封闭的几何状态，尚未实现游戏权限、碰撞和互动。
- 主体以 186.4×77.8m 工程基准表示；层高3.8m、净墙高3.4m仍是暂定值。跨层楼梯、货梯洞口和结构连接没有完成验证，外立面／屋顶也只是暂定体量。

Blender 保存后独立重开检查通过20层、冻结墙模块、每层房间名义数量及4F锚点；该检查不等于玩家通行、整栋结构或最终美术验收。三张图分别为外观、整栋剖视和4F局部。没有导入CAD几何作为美术模型，源脚本与坐标数据路径见下文。

---

# Cryo Building Blockout v1

Status: spatial verification blockout only. It is not playable, not a final exterior, and not final art.

## Scope

- One 20-standard-level cryogenic dormitory building: B4–B1 + 1F–16F.
- A frozen standard floor is reconstructed from `floor_layout.json` as independently editable Blender primitive modules. No FreeCAD geometry is imported or converted.
- Each floor retains the frozen wall, personnel-corridor, elevator-node and stair footprints; the non-hero rooms hold only logical closed-room envelopes and simple closed-door faces. They contain no pods or interiors. These faces are not final door art, permissions, collision, or game behavior.
- 4F `SW-01` is a provisional replacement anchor for the existing Godot Room 1, using its frozen 21×9.5 m bounds and D001 1.4 m door opening. It does not modify the Godot scene.
- B1–B4 are in a separately hideable collection. The roof and exterior are deliberately simple temporary massing, not a design decision.

## Files

- `source/build_cryo_building_v1.py` — reproducible Blender builder.
- `source/validate_reopen.py` — independent open/readback validation.
- `cryo_building_blockout_v1.blend` — editable Blender source (generated).
- `validation.json` / `reopen_validation.json` — static source and reopened-scene checks.
- `evidence/` — external overview, all-level cutaway, and 4F anchor screenshots.

## Provisional values and limitations

Storey height 3.8 m, wall height 3.4 m and slab thickness 0.10 m are current blockout values only. The model has not passed structural, route-playability, exterior-design, UV, lighting, final-art or Godot-integration review. The screenshots are inspection evidence, not final camera composition. The continuous machine core is an opaque inaccessible placeholder and may hide transfer detail; it does not certify freight/corridor connection between levels.
