# Room 1 地坪边界与舱基接触旧化 r8

2026-10-27。用户认为r7地面仍不够好看，要求四边墙脚接缝沿用墙面式沉积，同时在每个休眠舱的落地接触线与边角增加旧化。当前是待审候选，r7完整保留。

[同机位对照与巡检](preview.html) · [地面源层与位置校验](source/floor_quality.json) · [分层Aseprite](editable/) · [当前Blender源](room1_floor_contact_r8_packed.blend)

## 美术调整

- 保留连续统一蓝灰地坪和原大面材料变化；不加地砖、道路色带、新拼接线或无来源散斑。
- 四周真实墙脚增加连贯的像素沉积。深色接触根、灰蓝沉积肩部、断续灰白矿物边形成厚薄变化，轮廓使用固定的非周期阶梯变化。门洞处按实际开口中断墙脚沉积，门槛不画成一条厚脏带横封通路。
- 20个休眠舱的接触线来自r7 Blender源实际距地0–3.5cm的网格顶点轮廓；不是用舱盖AABB或手估矩形。每个舱沿底座接触线连续积旧，边角加宽、长边较窄，不在旧膜与底座间留固定干净隔离边。不同舱的厚薄与碎边不同。
- P03/P06/P13/P18四处旧漏液保留，三份漏液源层逐字节不变；新接触沉积放在漏液层下。液体成分、年代与剧情意义仍TBD。没有新增实时液体、碰撞或玩法。
- 墙图保持r6，舱体、门、人物、布局、UV、原灯带和曝光保持。新地面配套1024样本、2048线性HDR重新烘焙，采用原四发光面与现有连续UV2，避免继续借用换色前的反弹光。

当前图仍为1648×728、80 texels/m试值，不新增全项目像素规格。所有新增脏污分量都连接到真实墙脚或舱基，地面中央保留完整主面。

## 编辑源与复现

- `editable/floor_contacts_r8.aseprite`：7层，不含漏液；`editable/floor_contacts_leaks_r8.aseprite`：10层，含原漏液。两份母版重开导出与运行PNG精确一致。
- `source/floor_layers/`保留原3层材料＋4层新接触沉积＋原3层漏液。四个新增层分别是墙脚沉积、舱底接触、舱角累积、舱角矿物边；独立调整，不把原图压平覆盖。
- `source/read_footprints.py`只读r7源，输出`pod_footprints.json`；`source/build_floor.py`沿真实轮廓制图；`source/package_floor.lua`打包和重开导出；`source/check_floor.py`检查母版、尺寸、20轮廓、四边与新簇连接性。不存在漂浮的新增脏污分量。
- `scripts/dev/bake_room1_floor_contact_r8.py`保留几何／UV／四灯带，使用当前颜色图生成新irradiance和`room1_floor_contact_r8_packed.blend`。默认拒绝覆盖已有完成输出；明确重建需设置`ROOM1_FLOOR_CONTACT_R8_ALLOW_OVERWRITE=1`。`readback.py`重新打开实际打包工程验证，raw缺失时从packed图像读取。
- 本轮没有新增AI／PixelLab调用，没有复制参考作品像素。

## Godot对比

F6运行`scenes/dev/room1_floor_contact_r8.tscn`。默认新地面＋新配套光照。F切换原r7／新r8地面；I切换r7／r8光照；N检查颜色图，J回位，WASD移动。正式主入口不变，旧r5–r7场景保留。

对照A为原r7地面＋r7光照，B为新地面＋旧光照，C为新地面＋新光照。这样能单独判断地面绘制效果。截图保持同相机、1280×720、原曝光；Base Color仅作诊断，不能当成正式自发光。巡检另临时显示前墙并在拍后恢复剖切。

比较覆盖前后排左中右、普通舱底／边角、原四处漏液、墙脚四角、真实前墙、门槛与20舱总览。精确恢复与源包检查见`quality_check.json`和两份`capture_record.json`。新候选仍需用户判断沉积强度与整体观感，不宣称已通过最终美术审查。

运行包依赖当前Godot Shader、r6墙图与新r8地面，不能把裸GLB拖入当成完整材质效果；GLB仅作为原样几何／UV2载体，嵌入旧颜色不重写。可继续编辑的当前墙地材质已打包在Blender工程内。raw EXR、日志和缓存不上传；raw技术截图可通过本地重建复现。
