# 已筛选参考｜材料、构件、老化依据

返回[执行入口](../CRYO_BUILDING_ART_PRODUCTION_PACK.md) · [材料卡](MATERIALS_AND_AGEING.md) · [造型规格](COMPONENTS_AND_VARIANTS.md)

检索/核对：2026-11-10。这里不是让Codex再搜索选型的素材池，而是本包已经采用的参考依据。每项写明**借什么、不借什么**。现实产品的技术说明、项目档案事实和本包的未来设计推演必须分开。

图片使用公开来源外链供人工观察，没有将第三方原始照片打包进本仓库，也没有输入生成服务。外链失效时打开同项制造商页面，不把图片失效变成重新设计材料的理由。图片/商标权利归原作者，不能作为可分发游戏贴图或训练素材。

## 档案基线：这些不是本包的新创意

已读取源提交`dcd51fcaf79c73273c73be79dad707687d494a59`中的：

| 文件 | 本包使用的事实 |
|---|---|
| [AGENTS](../../../AGENTS.md)、[制作基准](../PIXEL_ART_PRODUCTION_STANDARD.md)、[PixelLab流程](../PIXEL_TEXTURE_WORKFLOW.md) | PixelLab主体＋Aseprite局部精修；1280×720审图、80原生像素/m；不能用程序旧化代替绘画 |
| [版本索引](../ROOM1_VERSION_INDEX.md) | r24墙/r26地/r28舱为当前已认可基线；r30门、4F v6比较仍待选择；不翻修已完成房间 |
| [楼梯材质小样](../experiments/cryo_stair_material_sample_v1/README.md) | 灰色哑光细矿物材质已定；首版偏花、quiet1过平；当前局部折中候选不是最终验收 |
| [建筑Brief](../CRYO_BUILDING_LOWPOLY_BRIEF.md)、[设施布局](../../CRYO_FACILITY_LAYOUT.md) | 16F＋B4、四区、四楼梯/人员电梯、冻结工程位置与范围；1F无大型接待厅 |
| [楼梯照明](../CRYO_STAIR_MOTION_LIGHTING_BRIEF.md) | 一体化感应灯带、提前增亮、停留保持、后方渐暗；亮于休眠室 |
| [电梯入口](../CRYO_PASSENGER_LIFT_ENTRANCE_BRIEF.md) | 电梯停电，门闭合，按钮/认证熄灭；仅独立CAUTION条继续工作 |
| [房门](../ROOM1_INTEGRATED_DOOR_ACCESS_BRIEF.md)与现行4F记录 | 房门视觉/灯语继承，不用早期触发方式覆盖后续E交互实现 |

以下产品只支持材料/构造参照，不证明本楼符合任何现实认证，也不提供80～90年无人维护的寿命结论。

<a id="r01"></a>
## R01｜KEIM Innostar：室内矿物漆的哑光面

[制造商产品页](https://keim-usa.com/product-categories/interior-paint/innostar/)

**资料支持**：矿物sol-silicate室内漆，强调低光泽哑光表现及可清洁的耐擦洗性能。**本包采用**：M01的面层类别解释；原生画面仍直接继承r24，不能因参考现代产品而换颜色或变成普通住宅乳胶漆。**不外推**：具体老化百分比、未来材料配方与无人维护寿命。

<a id="r02"></a>
## R02｜Sika Floor Systems：连续地坪是系统，不等于瓷砖

[制造商体系页](https://www.sika.com/en/construction/floor-systems.html)

**资料支持**：连续地坪可采用树脂、水泥基及复合体系。**采用**：M02保留“连续密封复合地坪”的材料逻辑，并与矿物楼梯踏面区分。**不采用**：商业空间鲜艳色彩、镜面效果、照片中的分区线；本项目r26不是这家产品的真实安装记录。

<a id="r03"></a>
## R03｜Sikafloor-3 QuartzTop：矿物耐磨面原型

[制造商产品页](https://gbr.sika.com/en/construction/flooring/curing-agents-dryshakes/sikafloor-3-quartztop.html)

**资料支持**：矿物干撒耐磨硬化面用于整体地坪。**采用**：M03灰色、致密、细矿物的材料身份；游戏中的楼梯另按既有踏步几何构造。**不采用**：把地坪施工工艺机械复制为本楼楼梯施工方案，或大颗粒抛光水磨石。防滑可读性由本包踏鼻/材质/灯光共同呈现，不由一张产品图证明。

<a id="r04"></a>
## R04｜ナカ工業＋Kegel Product：连续可握扶手与隐藏照明

[ナカ工業不锈钢扶手照明](https://www.naka-kogyo.co.jp/products/led-sus-handrail.html) · [椭圆/圆形握持截面](https://www.naka-kogyo.co.jp/products/vinilane-slim.html) · [Kegel Product 实际楼梯转角](https://www.derledhandlauf.de/projekte/studienakademie-bautzen)

**资料支持**：不锈钢连续扶手可嵌入照明，直径/椭圆握持截面与墙/立柱安装均有实际产品。**采用**：HR两款的连续握持线、隐藏支架、金属层次和转角；L-01采用独立墙内灯槽，**不照抄照片把灯装到所有扶手上**。本包高度/护栏构造为试作参数，不是从产品照片测得的法规尺寸。

![连续扶手、转角与隐藏支架；照片©Kegel Product，外链观察](https://www.derledhandlauf.de/assets/images/2/img_6091-1db2d5a1.jpg)

![矿物楼梯与侧向照明的整体关系；照片©ナカ工業，外链观察](https://www.naka-kogyo.co.jp/cmsnaka/wp-content/uploads/2019/11/led_sus_02.jpg)

不借户外植被、暖黄光、玻璃护栏或照片中的繁密石材分缝。ナカ工業页面也提示现实灯具需要检修/更换，不能据此宣称本游戏的残余灯能无维护运行数十年。

<a id="r05"></a>
## R05｜ナカ工業 Hi-Step Art：薄型踏鼻层次

[制造商产品页](https://www.naka-kogyo.co.jp/products/hi-step-art.html)

**资料支持**：薄型踏鼻构件能在台阶前缘提供独立的防滑表面和收边，页面示例厚度4mm。**采用**：M10位置与薄层次，试作中改为齐平嵌入；45mm宽度为本包设计值。**不采用**：其树脂配方、现成品牌颜色或“贴上去就已满足安全”的结论。

![踏鼻的薄边与独立摩擦面；照片©ナカ工業，外链观察](https://www.naka-kogyo.co.jp/cmsnaka/wp-content/uploads/2019/11/hi_step_06.jpg)

<a id="r06"></a>
## R06｜Hörmann Steel and Fire-Rated Doors：实体分隔门的构造分工

[制造商钢门页](https://www.hormann.co.uk/industry-commerce-and-public-authorities/doors/steel-doors/)

**资料支持**：钢/不锈钢门可以组合不同防火、防烟与五金功能。**采用**：FD的实体门壳、固定框、密封与机械释放应分别存在。**不采用**：把产品认证搬给游戏模型；不引用未核实的耐火分钟数。FD-A/B的分扇比例、维护带和配色是本包新设计，不是该厂商产品复刻。

<a id="r07"></a>
## R07｜Wittur Landing Doors：电梯门分件与收纳逻辑

[制造商门系统总览](https://www.wittur.com/en/elevator-components/landing-doors.aspx)

**资料支持**：门板、门框、门槛及中分/侧收/套叠方式是不同构造因素，不能只画一道黑缝就当完整设备接口。**采用**：EL-A中分、EL-B三片侧收在关闭态的可读层次。**不采用**：上方真实驱动机械外露、现代轿厢内部、圆形豪华观光门、楼层面板；本项目完全不需要展示运行机制。

<a id="r08"></a>
## R08｜Rieder concrete skin：薄矿物围护板与暗固层

[制造商材料/安装页](https://rieder.cc/concrete-skin) · [材质说明](https://rieder.cc/material-fibrec)

**资料支持**：玻纤增强矿物板用于通风幕墙围护，可有可见或隐藏固定，表面有多种低光泽纹理。页面产品厚度13mm；本包美术试作15mm并非同一产品技术数据。**采用**：M06的大块完整矿物面、转角连续性和隐蔽支承。**不采用**：参考建筑的窗洞、暖红颜色和全部现代节点；本楼保持无普通窗洞。

![围护板与隐蔽支承，不是裸露最终立面；图片©Rieder，外链观察](https://framerusercontent.com/images/r5w2h2YBh7E0NQzIWC24yd377DM.png?height=1280&width=1049)

照片中露出的骨架是构造参考；最终候选应封闭，不做施工中的建筑。

<a id="r09"></a>
## R09｜RHEINZINK prePATINA：蓝灰金属钝化表面

[制造商表面页](https://www.rheinzink.com/products/materials-surfaces/prepatina/) · [材料耐久介绍](https://www.rheinzink.com/future-ready-building/sustainable-planning-and-building/durability/)

**资料支持**：钛锌表面可形成/预制蓝灰或石墨灰的哑光钝化外观，并用于屋面、立面、压顶。**采用**：M07的低反射蓝灰、折板/收边与细微表面变化。**不采用**：将钝化层画成钢铁红锈或大片掉漆；厂商耐久宣传不等于本楼已完成寿命验证。

<a id="r10"></a>
## R10｜Canadian Conservation Institute：痕迹需要环境与材料成因

[金属保存](https://www.canada.ca/en/conservation-institute/services/preventive-conservation/guidelines-collections/metal-objects.html) · [陶瓷与玻璃保存](https://www.canada.ca/en/conservation-institute/services/preventive-conservation/guidelines-collections/ceramics-glass-preventive-conservation.html)

**资料支持**：水、湿度、污染物和积尘会影响金属腐蚀；沉积/污染也可能进入陶瓷玻璃的孔隙、裂隙与表面。**采用**：区分室内凹边沉积、旧接触、室外雨淋，拒绝无因污斑。**边界**：这是馆藏保护的一般行为依据，不是未来建筑涂层的磨损模型；本包没有从年代直接推算失效比例或断裂强度。

<a id="r11"></a>
## R11｜Shin-Etsu：硅橡胶不是天然橡胶老化纹理

[橡胶材料类别](https://www.shinetsusilicone-global.com/products/type/rubb_comp/index.shtml) · [建筑密封材料说明](https://www.shinetsu.co.jp/en/products/functional-materials/silicone-sealant-for-construction/)

**资料支持**：硅胶体系的耐候、温度/紫外线/臭氧抵抗能力与普通有机橡胶不同。**采用**：M08以压接与嵌灰为主，不默认所有条都干裂。**不外推**：每个配方相同、没有老化、数十年密封性能仍合格；实际压缩残余和维护史未知。

<a id="r12"></a>
## R12｜NABCO Breakout：出口要有断电以外的疏散逻辑

[制造商产品页](https://nabco.nabtesco.com/en/solutions/products/breakout/gt-1175bo-foslm/)

**资料支持**：自动门可以具有独立的应急外开/机械疏散方式，安全退出不只等于“认证正常且电机有电”。**采用**：EN/FD保留机械释放的设计原则。**不采用**：照片的玻璃商业门、产品尺寸、110N等具体性能值；本包EN两款是新的不透明双扇外开方案，不能标为NABCO同款或已经通过测试。

## 看参考时的三个问题

1. 观察到的是材料固有色/制造纹理，还是当时的照明投影？后者不能烘进新颜色图。
2. 痕迹是接触、沉积、雨淋还是实际破坏？只复制形状而没有成因会重犯旧版“污迹贴片”的问题。
3. 这个产品的构造能解释本包某个可见细节吗？若不能，不因为“很科幻”给建筑加部件。

本包没有使用未经核实的80年损坏百分比，没有把商家寿命/认证转写成项目事实，也没有新增已发生的漏水、火灾或坍塌剧情。
