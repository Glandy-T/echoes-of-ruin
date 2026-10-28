# Room 1 主角比例与舱号试排 r1

打开 `scenes/dev/room1_hero_scale_review_r1.tscn`，F6 运行；Y 切换原尺寸与缩小 15%，默认缩小版。E 调查、Enter 翻页、WASD 移动。此场景继承本地 `room1_dialogue_adapter_review_r1.tscn`，正式游戏主场景未切换。

角色使用原始像素帧，内容高度由 1.65m 调为 1.4025m，脚底位置不变；当前只改变 Sprite3D 视觉尺寸和相应辉光遮挡副本，原胶囊碰撞和接触阴影仍按 1.65m 测试体。等比例方案确认后需重新调整并验证碰撞、阴影、舱体开盖占用保护和交互距离，不能视为最终人物物理比例。

旧舱按场景 P01–P20 的名称，在运行时独立生成端面和舱盖编号 01–20；P12 沿用新 v8 的 12。没有改写原 GLB、贴图或可编辑母版。这是审查场景中的临时差分，19个旧舱仍是旧模型，没有推广新舱。自动核验逐个检查旧舱两处数字像素，以及主角两种尺度；P12 保留。实际画面查看了游戏机位的后排及前排 P03 舱盖，其他端面和镜像问题仍需全室逐面审查。

`evidence/original.png`、`candidate.png` 是同机位 Godot 实际渲染；`front_row_check.png` 是临时技术机位。`capture.gd` 可重新生成；`scripts/dev/verify_room1_hero_scale_numbers_r1.gd` 可做无头核验。没有修改主场景、资产母版、房间几何和光照烘焙。
