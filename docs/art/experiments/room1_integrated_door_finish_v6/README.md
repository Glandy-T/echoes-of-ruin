# Room 1 主门 v6：弱化门框与旧化贴图审图

状态：**独立候选，等待美术审查；未替换正式场景**。以 [v3](../room1_integrated_door_v3/README.md) 为结构、灯语、滑动和镜头基准。按反馈降低常态门框存在感，同时使门面做旧在当前游戏镜头里可辨。旧 v4 提亮和 v5 过净样本均保留作对照。

## 调整

- 待机、认证和拒绝时，门洞内侧只保留跟随墙面亮度衰减的三边中性窄收口；底边不出现额外亮线。门叶侧面的 85 mm 厚度也随高度变暗，避免底部常亮。
- 认证通过期间仍恢复 v3 的完整四边绿灯；无权限只由猫眼高度的小状态窗发红。
- 门面继续使用现行 r6 矿物墙材的色系与 80 texel/m 密度。上沿沉积取自后墙顶部接缝附近的像素层，滑动接触痕落在门叶左右密封边，微量积灰留在小窗凹口，底边只留窄封条痕迹。没有随机污点，也没有把固定墙脚的大块污积搬到移动门叶上。
- 不改门尺寸、门洞、休眠舱、房间照明、交互状态机、开闭速度、碰撞和走廊灰模。

## 文件与审图

- [同机位对比页](preview.html)：v3、v5、v6 关闭状态及 v6 四种灯语状态。截图由 Godot 4.6.2 Compatibility 模式实际导出，1280 × 720。
- [Aseprite 四图层源](editable/door_front_v6.aseprite)、[图层生成脚本](source/build_pixel_layers.py)、[Aseprite 打包脚本](source/package_layers.lua)。
- [运行时 PNG](../../../../assets/art/room1_integrated_door_finish_v6/door_front.png)、[Godot 审图场景](../../../../scenes/dev/room1_integrated_door_finish_v6.tscn)、[门脚本](../../../../scripts/dev/room1_integrated_door_finish_v6.gd)、[收边材质](../../../../scripts/dev/room1_integrated_door_finish_v6_reveal.gdshader)。保留 v3 的 GLB 和原后墙贴图。

重新生成贴图：先运行 `source/build_pixel_layers.py`，再以 Aseprite 批处理运行 `source/package_layers.lua`。运行时 PNG 与 Aseprite 回读 PNG 逐像素一致。执行 `scenes/dev/room1_integrated_door_finish_v6_capture.tscn` 可重拍证据图。

`runtime_validation.json` 记录 Godot headless 检查通过：待机／认证／拒绝时底边不亮，授权通行期间四边绿灯全部恢复，且审图门确实引用本版 PNG。检查场景为 `scenes/dev/room1_integrated_door_finish_v6_verify.tscn`。五张截图分别覆盖关闭、黄灯、绿灯开门中、绿灯开门后和拒绝红窗。它只验证本轮状态与画面，不代表完整多人防尾随和安全避夹功能已实现。

## 审查边界

常态三边收口是未通电的物理槽位；它不负责照明。实际需要在游戏镜头核对的重点是：门边是否仍显得像额外安装的框、旧化是否与墙面协调、以及通行绿灯是否足够细但可读。此候选没有解决以后多主体尾随、安全避夹、停电疏散规则。
