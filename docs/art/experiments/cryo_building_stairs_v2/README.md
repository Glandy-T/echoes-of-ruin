# 单栋休眠楼消防梯灰模 v2

基于 [v1 空间骨架](../cryo_building_blockout_v1/README.md)另存的可编辑 Blender 工程。它使用 GitHub main 现行的 [楼体 Brief](../../CRYO_BUILDING_LOWPOLY_BRIEF.md)和冻结 `docs/cad/cryo_standard_floor/v3_trim/floor_layout.json` 的平面坐标；没有导入或复制 FreeCAD 几何。**楼梯断面、踏步和层高仍是灰模验证值，不是正式建筑设计。**

## 本轮内容

- 保留 16F＋B1～B4、每层 48 室、四个互不相通的人员分区和四座消防梯。v1 工程未覆盖。
- 移除每层四个实心楼梯占位，在 20 层逐层裁开对应楼板；每座楼梯均有 20 个入口平台、19 段跨层双跑梯段。西／东与北／南仍按两组四座理解。
- 按冻结 CAD 的 96 个门洞／层建立门板灰模；4F 的主角房 `D001` 和通往西梯的 `D077` 保持开放，用于空间路径检查。其余门板只表示暂时不可进入，尚无芯片权限逻辑或开门动画。
- `SW-01` 仍是可替换的 Room 1 技术锚点；仅用冻结路线图检查 `SW-01 → SW_C0 → 西侧消防梯`。现有 Room 1 游戏场景尚未实例化进楼体，叙事上也不依赖该房号。
- 1F 对外出口未在冻结标准层图中定位；此版路线到达 1F 西梯间为止，没有虚构出口或其他楼层的可进入室内。

## 查看

- [三张截图并排查看](preview.html)
- [完整 20 层 Blender 工程](cryo_building_stairs_v2.blend)
- Godot 静态导入检查场景：`scenes/dev/cryo_building_route_review_v2.tscn`。只含 4F 平面及西梯至 1F 的轻量 GLB，不替换正式主场景；该场景不支持玩家行走。
- Godot 导入 GLB：`assets/art/cryo_building_stairs_v2/cryo_building_route_4f_to_1f_v2.glb`。

Blender 原始 v1 文件 SHA-256 与本轮新工程保存的来源哈希相同。独立重开检查见 [reopen_validation.json](reopen_validation.json)：80 个梯井断面无遮挡、76 段跨层梯段、4F 主角房到西梯的冻结路线图可达，均通过。Godot 4.6.2 编辑器导入 GLB 成功；在正常权限下运行此审查场景两帧，退出码为 0。**尚未进行真实人物碰撞、上下楼、门权限或 1F 室外出口的游戏运行验收。**

## 下一步

将现有 Room 1 场景按 `x=0–21m, y=4.2–13.7m` 的冻结房间位置与 4F 楼体对齐，避免两个场景的同一墙地重复显示；然后给 4F 授权走廊和西梯配置游戏碰撞与移动测试。1F 出口门位需要单独确定，之后才能验收 Room 1 到室外的完整路径。其他楼层室内继续保持锁定。主门外观、扶手和最终材质仍属后续美术工作。
