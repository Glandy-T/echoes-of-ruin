# Room 1 主门明度与收边 v4（视觉退回，仅保留对比）

**2026-10-29 审图结论：不采用 v4。** 用户指出整扇门比房间其他表面亮，底部出现不自然的“光源感”。后续门美术继续从 [v3](../room1_integrated_door_v3/README.md) 的色阶出发；v4 的 Shader 与待机灯槽设置不能当作新默认。

基于 [v3](../room1_integrated_door_v3/README.md) 的同一房间、门洞、门叶几何、像素贴图和单人自动通行逻辑。本版只测试门面、门底与门洞暗收边的视觉明度；v3 保留作为基准。

## 判断依据

洁净室的齐平滑门可以采用与墙相近的表面色，门框嵌入隔墙，门叶与墙之间靠窄密封边读出运动关系。实物参考：[Dagard Ultra Clean 的齐平门系统](https://www.dagard.com/clean/ranges/ultra-clean)、[ASSA ABLOY Hermetic 滑门](https://www.assaabloy.com/in/en/solutions/products/automation-doors-and-security-entrances/automatic-doors/airtight-doors/hermetic-sliding-doors)。这里只借鉴构造关系，不复制医院门上的观察窗、把手、标识或具体配色。

原设想是把门面比墙提亮、保留门底材料色，并在待机时显示门框内侧的实体收边。实际 Godot 同镜头表明判断错误：v3 上部与墙面亮度已经很接近。v4 又全局提高门板明度，把无光照 Shader 的底部手工亮度项从约 `0.085` 再增加 `0.125`，并让底侧灯槽在熄灯时仍然可见。底部于是比邻近墙脚亮得多，像自己在发光。这是材质和灯槽的视觉假象，场景中没有新加真实光源。

对实际截图的同位置取样：门底接近地面处，v3 约 `(5, 8, 7)`、v4 约 `(26, 35, 32)`；邻近墙脚约 `(6, 12, 13)`。因此 v4 的行为验证通过不代表美术通过。下一次应检查门洞构造和密封收口，不再靠整体提亮或门底补光解决违和感。

## 修改边界与查看

- [同镜头 A/B 与开门状态](preview.html)，实际 Godot 1280 × 720 截图。
- 本版复用 v3 的可编辑 `door_front_v3.aseprite`、运行 PNG 与 GLB。色阶修改在独立 [v4 Shader](../../../../scripts/dev/room1_integrated_door_v4.gdshader) 和 [v4 审图脚本](../../../../scripts/dev/room1_integrated_door_v4.gd) 中；没有改动原版像素源文件。
- Godot 试用场景：[room1_integrated_door_v4.tscn](../../../../scenes/dev/room1_integrated_door_v4.tscn)。同尺寸门洞、单扇侧滑、碰撞与认证状态沿用 v3；正式场景未切换。
- [运行验证结果](runtime_validation.json) 只检查 v4 新增的待机可见灯槽及黄／绿／红状态。v3 原有通行和碰撞验证仍见 v3 报告。

v4 仅作为被否定的 A/B 记录；正式场景没有切换到 v4。
