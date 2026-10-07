# Room 1 工程图与空间验证

最新3D交付：**v2 3D空间验证 / 2026-10-07**。任务依据`501140a`，阶段标记为`ROOM 1 SPATIAL BLOCKOUT ACCEPTED`，仅覆盖静态闭舱空间比例与几何；人体动作、开盖及最终美术身份仍待验证。

继承v2全部平面与舱体，独立模型测试3.40 m墙高、1.40×2.40 m真实门洞。8张原生视角覆盖门口、纵向轴线、横向左右、舱间操作位、开顶斜俯视与俯视。90个有效实体，新增碰撞0，80个舱体分层的位置与形状不变，原v2全部交付文件哈希未改变。

- [3D FreeCAD 可编辑文件](blockout_v2/room1_3d_blockout_v2.FCStd)
- [3D验证结果与逐项空间判断](blockout_v2/README.md)
- [离线视角索引](blockout_v2/VIEW_GALLERY.html)
- [相机与验证数据](blockout_v2/visual_blockout_validation.json)
- [3D交付包](blockout_v2/room1_3d_blockout_v2_delivery.zip)

![Room 1 3D门口人视角](blockout_v2/evidence/visual_blockout/01_doorway_human_view.png)

![Room 1 3D开顶斜俯视](blockout_v2/evidence/visual_blockout/05_room_isometric_open_top.png)

0.70 m舱间位可容纳单人静态尺度柱，但剩余余量较紧，不能当作上下舱或转身已验证。3.50 m横向通道较宽敞；门后展开自然，3.40 m高度未见明显失衡。本轮未开始标准层。

当前交付：**v2 / 2026-10-07 / PROVISIONAL，待设计审阅**。

已依据[工程简报](ROOM1_ENGINEERING_BRIEF.md)提交`6ddc2ddf2eac0eef5aecc959120a24d041afe7da`完成v2。仅将房间外包宽20.00→21.00 m、中央纵向通道1.60→2.40 m、后墙人员门1.60→1.40 m。房间深度9.50 m、20舱四区各5、舱体分层形状、3.50 m横向通道与0.70 m舱间距沿用v1。

室内净尺寸20.60×9.10 m；左右墙边余量各1.05 m，前后各0.50 m。居中的1.40 m门洞与2.40 m纵向通道之间两侧各展开0.50 m。

- [FreeCAD 可编辑源文件](v2/room1_engineering_v2.FCStd)
- [A2三页工程图 PDF](v2/exports/room1_engineering_v2.pdf)
- [完整交付 ZIP](v2/room1_engineering_v2_delivery.zip)
- [参数、v1对照、范围与再生成说明](v2/README.md)
- [全部参数与验证 JSON](v2/cad_validation.json)
- [GUI原生尺寸与七项参数联动](v2/qa/gui_validation.json)
- [保存后独立回读与舱体几何对照](v2/qa/saved_validation.json)
- [文件哈希清单](v2/manifest.json)

89个全约束草图、86个有效实体，正体积实体碰撞0。对照v1，只有上述三项输入参数改变；80个舱体分层平移对齐后形状一致，v1源文件保留。

**验证边界：**仅验证静态闭舱几何。开盖扫掠、人体转身/上下舱、辅助操作、搬运更换、消防机电与室内净高仍待验证。3D图中1.3 m墙高为剖切显示值。本版尺寸为设计测试值，未扩展标准层、整栋楼或园区。

## 总平面 A301

![Room 1 v2 A301](v2/qa/plan-1.png)

## 单舱分层 A302

![Room 1 v2 A302](v2/qa/plan-2.png)

## v1 / v2 尺寸对照 A303

![Room 1 v2 A303](v2/qa/plan-3.png)

## 原生实体轴测

![Room 1 v2 原生轴测](v2/qa/room1_isometric.png)

## 历史版本

- [v1说明与实尺验证](v1/README.md)：20.00×9.50 m外包，纵向通道1.60 m，后门1.60 m。
- [v1 FreeCAD](v1/room1_engineering_v1.FCStd)、[v1 PDF](v1/exports/room1_engineering_v1.pdf)、[v1 ZIP](v1/room1_engineering_v1_delivery.zip)。
