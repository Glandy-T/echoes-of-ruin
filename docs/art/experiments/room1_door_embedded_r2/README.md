# Room 1 主门轮廓候选 r2

这是一版待审的嵌入式单扇门轮廓：保留门洞和原有芯片扫描、横向滑开与碰撞，门面仅有一块浅层分区和窄收边。F6 运行 `scenes/dev/room1_door_embedded_review_r2.tscn`；0 到门前，U 切换测试芯片，L 切换墙灯。旧标题入口仍然使用 r1。

[闭合、关灯、扫描、开启截图](preview.html)。门面目前只是程序生成的纯色几何测试，没有像素贴图、UV母版或配套重烘焙；新门通过随灯带开关变化的临时材质近似受光，不能当成全室光照验收。门外仍是黑色的下一场景占位。此版只检查门造型，不代表房间整体美术或光照已完成。

实际运行验证检查识别、门扇位移、碰撞体随门同步和关闭循环；四张截图检查了开合及墙灯状态。后续需先审定造型，再制作像素表面与可编辑源，完成全室光照巡检后才适合合入正式入口。

---

# Room 1 main door — embedded candidate r2

This is an independent review scene, not a replacement for the existing `r1` door scene.

- Scene: `scenes/dev/room1_door_embedded_review_r2.tscn`
- Script: `scripts/dev/room1_door_embedded_review_r2.gd`
- Validation: `scripts/dev/verify_room1_door_embedded_r2.gd`
- Runtime evidence: `evidence/closed.png`, `scan.png`, `open.png`

## Scope

The r1 automatic recognition, 1.5-second scan, three-second single-panel slide, collision movement, temporary exit boundary, and door opening size are reused without changing their values.  The rejected black visual placeholder is hidden only in this instance and replaced with one muted cool-grey slab plus a shallow inset and four narrow reveal strips.  It has no handle, wall panel, screen, sign, or new decoration.

The opening remains black because the next room is not implemented; the black opening and exit boundary are retained deliberately.  `scan` is inherited temporary interaction feedback, not a finalized effect.

## Lighting boundary

This candidate creates a runtime door mesh.  It does **not** rebake Room 1 wall/floor lighting or claim that inherited bake as an r2 lighting result.  Its door material follows the established Room 1 ribbon-light state so it dims with `L` (`evidence/lights_off.png`); this is a runtime readability approximation, not a lightmap.  The full-scene lightmap/UV gate remains `docs/art/ROOM1_LIGHTMAP_QA.md` for any future production merge.

## Run

Open the r2 scene and run it. `0` teleports to the door; `U` toggles the test chip; the normal `WASD`/`E` controls remain inherited.  In headless validation:

```powershell
& 'C:\文件类\GODOT\Godot_v4.6.2-stable_win64_console.exe' --headless --path . --script res://scripts/dev/verify_room1_door_embedded_r2.gd
```
