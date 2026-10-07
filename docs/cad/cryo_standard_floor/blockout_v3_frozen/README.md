# 标准休眠层整层 3D Blockout / 0E 修复与冻结

**STANDARD FLOOR SPATIAL BLOCKOUT ACCEPTED / FROZEN FOR NEXT BUILDING STAGE**

依据提交 `b53aa9b8e38c7c423703dd946c2ba88d44b9ab37`，在已接受 `b84e34c` 基础上只修井道楼板、两侧保护廊楼板和南侧双墙缝。

- [原生可编辑3D](standard_floor_blockout_v3_frozen.FCStd)，745个原生对象；48室/960舱，四代表室完整闭舱、其余44室为真实舱外包；全部共享模板内置，打开不依赖外部CAD。
- [13个实际FreeCAD视角](VIEW_GALLERY.html) / [图册预览](VIEW_CONTACT_SHEET.png)：保留原十视角，新增东西电梯-楼梯连接、轿厢参照隐藏的四井道检查。所有墙体保留，相机配置与原始Coin相机参数随附。
- [修复验证](qa/cleanup_validation.json) / [原生模型读回验证](blockout_validation.json) / [冻结记录](FREEZE_STATUS.json) / [交付ZIP](standard_floor_blockout_v3_frozen_delivery.zip)。

四个人员井道：从结构板及前室薄地面参照中扣除原净井道2.10×2.40m，保留井壁脚下支承；四个轿厢地面仍为独立LiftCars组，隐藏即可看真实空洞。东西保护廊各两段实际补板，不改变原边界；南侧X[-2.60,-2.40]与[188.80,189.00]的Y[28.00,28.20]墙缝按原墙端点闭合。总平面中仅增加这两片墙面积0.08m²，没有删墙或移动开口。

实际保存文件中：四井道结构板/步行地面覆盖为零；四保护廊段完整覆盖；142段人员路径有连续结构板支承，进入独立轿厢的边单独排除；所有94个实体门洞/绕行口净高2.40m、8条人员廊净空、88个梯步位置、48室舱包络均通过。所有形状有效，房间/分区/梯井/楼梯/四货梯/Q/机器核心/外包/路径与上一版完全一致。2D同源修复记录与原生CAD另附于v3_frozen。

四座U梯为每梯24级，11踏面/跑加平台台阶；中间平台+1.90m、上平台+3.80m，楼梯井不封顶，未制作下一层结构。主区顶板默认隐藏。墙高3.40m、门高2.40m、层高3.80m、楼板厚0.10m、人形尺度柱1.68×0.45m均为暂定空间测试值。仅单层灰模，没有最终材质、场景灯光、外立面或多层堆叠；门扇动画/扫掠按0E.4留待详细设计。

重建流程：先重建相邻v3_frozen 2D数据，再运行build_blockout.py、原生GUI渲染宏、validate_blockout.py与check_cleanup.py；图面复核后才能运行v3_frozen/mark_freeze.FCMacro。重建需历史Room1闭舱源，打开本FCStd无需源文件。布局冻结后仅遇到整栋堆叠、结构或游戏相机的明确冲突再修改。
