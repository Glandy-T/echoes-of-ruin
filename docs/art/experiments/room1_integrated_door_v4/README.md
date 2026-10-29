# Room 1 主门明度与收边 v4（审图候选）

基于 [v3](../room1_integrated_door_v3/README.md) 的同一房间、门洞、门叶几何、像素贴图和单人自动通行逻辑。本版只测试门面、门底与门洞暗收边的视觉明度；v3 保留作为基准。

## 判断依据

洁净室的齐平滑门可以采用与墙相近的表面色，门框嵌入隔墙，门叶与墙之间靠窄密封边读出运动关系。实物参考：[Dagard Ultra Clean 的齐平门系统](https://www.dagard.com/clean/ranges/ultra-clean)、[ASSA ABLOY Hermetic 滑门](https://www.assaabloy.com/in/en/solutions/products/automation-doors-and-security-entrances/automatic-doors/airtight-doors/hermetic-sliding-doors)。这里只借鉴构造关系，不复制医院门上的观察窗、把手、标识或具体配色。

v3 关门图中，门面顶部已接近墙色，但门叶侧面材质接近黑色、门底亮度塌到黑色，导致整个门洞读起来像一个矩形暗孔。v4 让门面比墙略亮一阶，门底保留可见材料，门叶实体侧面改为深灰绿色。内侧灯槽在熄灯时仍显示为极窄、无发光的实体收边；授权通行时仍为整圈绿色细灯。

## 修改边界与查看

- [同镜头 A/B 与开门状态](preview.html)，实际 Godot 1280 × 720 截图。
- 本版复用 v3 的可编辑 `door_front_v3.aseprite`、运行 PNG 与 GLB。色阶修改在独立 [v4 Shader](../../../../scripts/dev/room1_integrated_door_v4.gdshader) 和 [v4 审图脚本](../../../../scripts/dev/room1_integrated_door_v4.gd) 中；没有改动原版像素源文件。
- Godot 试用场景：[room1_integrated_door_v4.tscn](../../../../scenes/dev/room1_integrated_door_v4.tscn)。同尺寸门洞、单扇侧滑、碰撞与认证状态沿用 v3；正式场景未切换。
- [运行验证结果](runtime_validation.json) 只检查 v4 新增的待机可见灯槽及黄／绿／红状态。v3 原有通行和碰撞验证仍见 v3 报告。

门色、门框细度和其他镜头尚待美术审查；此候选不是最终主门。
