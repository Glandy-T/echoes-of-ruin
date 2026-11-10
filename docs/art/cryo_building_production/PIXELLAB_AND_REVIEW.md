# PixelLab作业、组装与审图交付

返回[执行入口](../CRYO_BUILDING_ART_PRODUCTION_PACK.md) · [材料](MATERIALS_AND_AGEING.md) · [造型](COMPONENTS_AND_VARIANTS.md)

## 1. 制作分工不变，交付范围扩大为本包列出的全部候选

执行现行[PixelLab工作流](../PIXEL_TEXTURE_WORKFLOW.md)与[像素制作基准](../PIXEL_ART_PRODUCTION_STANDARD.md)。PixelLab负责新主体材质及有依据的旧化，Aseprite允许局部像素精修/字形/UV边界整理。脚本可建低模、画精确导图/区域遮罩、排版与验证；**不画程序污斑、柏林噪声、正弦色差或粗多边形替代主体绘画**。

使用仓库中已验证的PixelLab连接方式，先检查当前可用接口、尺寸与余额。不要重新部署插件、购买或升级套餐；不要把历史每次10点/15点当作当前所有请求的费用。开始前生成`generation_plan.json`，逐项记录预计调用和当前实际计费口径；超过现有额度的项不偷换工具，保留缺项并继续无须生成的建模/复用作业。此文档本身未调用生成服务。

## 2. 先导出项目自己的输入，不上传第三方照片

每个生成任务都保存：

- `guide.png`：正交表面/UV平面导图，标清主面、边条、真实接缝、保护区，不含灯光投影；使用本包配色和自己建的几何。
- `edit_mask.png`：本次允许绘画的区域；E0/E1/E2/E3/E4区域说明存JSON，不把标签烧进最终贴图。
- `style_reference.png`：只使用项目自有r24/r26或当前已认可素材的原生裁片；r24裁片的授权见既有楼梯小样。参考区域若与生成画布并排，最终导出必须排除该区域，核查服务是否误改保护区。
- `prompt.txt`、请求元数据、原始返回图、实际用量。令牌/账号凭据不写入这些文件或Git。

现实产品照片、外部建筑摄影及Pixel Canals截图只在参考文档中观察。不能上传它们当img2img输入，也不能直接从图片裁纹理贴进游戏。

## 3. 原生像素尺寸规则

新资产主要表面按80原生创作像素/m设计，`有效宽px=round(实际展开宽m×80)`，高度同理。生成服务需要特定画布时，只补边/拆图，不先降分辨率再最近邻放大充数；记录有效内容窗口与物理覆盖范围。

| 表面 | 有效内容示例 | 注意 |
|---|---|---|
| 1.8m×0.30m踏面 | 144×24px | 从当前矿物母材质原生取样，不为每级新生成 |
| 1.8m×约0.158m立板 | 144×13px | 台阶高度来自工程，不反过来为整数像素改几何 |
| 3.8m×1.8m平台 | 304×144px | 不把192×256矿物图整体拉满平台；保持密度、检查重复接边 |
| 45mm踏鼻 | 约4px深 | 原脚本将0.2m贴图区压成45mm的旧映射不是新密度标准 |
| 门面 | W×H分别乘80 | 各片门从同一正交导图分区，文字/图标另层 |
| 直径42mm圆管 | 周长约0.132m，即约11px环向 | 长向仍按80px/m；不要给每个小面单独整张图造成密度乱跳 |
| FA-A矿物面板 | 约256×101px模数，缝另计 | 可在更大服务画布中保留有效窗口，不插值补细节 |
| FA-B层高板 | 约96×304px模数，缝另计 | 远景允许mipmap/简化策略单独检查，不能把立面纹素无限加大 |

示例只说明计算方法；最终必须对实际UV展开测量，尤其斜面、折边、扶手转角。颜色纹理Nearest，光照图线性；沿用当前连续照明和低高光，不新增全屏色阶化/CRT/降分辨率滤镜。

## 4. 有限生成任务表

| 作业ID | 交付 | 输入/现成来源 | 次数范围 |
|---|---|---|---|
| J00 | M01、M02、M03复用清单 | r24、r26、楼梯当前局部折中稿 | **0次新生成**；只读原生素材/检查来源 |
| J01 | M04不锈钢长条母材质1张 | 自制3.2×0.8m平面导图 | 初次1张，必要时针对问题修正1次 |
| J02 | M05-L/M05-D各1张涂层金属底材 | 自制3.2×3.2m导图，分别指定色板 | 初次共2张，最多各修正1次 |
| J03 | M06普通面3张＋节点面1张＋雨痕面1张 | 自制立面表面/接缝/滴水起点导图 | 初次共5张，必要时仅修失败项；不将翻转算新原图 |
| J04 | M07锌系覆层1张 | 自制折板展开，不带真实投影 | 初次1张，必要时修正1次 |
| J05 | FD-A/B、EL-A/B、EN-A/B正面表面图各1组 | 各候选已锁定几何的正交导图＋J02自有底材 | 初次6组；每组有效画布不足则按原生尺寸拆分，记录真实请求数 |
| J06 | M08、M09、M10及精确标识 | 既有项目门/灯带/踏鼻可用裁片＋Aseprite局部整理 | 默认0次；不能因纯色窄条再抽整图 |

初次计划共15个新画面任务（服务接口若需拆分，实际请求数另记），不是保证消耗15点。优先共享材质，不为HR-A/B分别重画两套不锈钢，也不为每层/每扇门重新调用。

**不允许因为某个方案“看起来更好”就省略另一款。**完成所有候选后再让用户选择。额度/工具确实不足时，按J01→J02→J04→J03→J05顺序完成可用项，其余清楚标缺；不能把缺图静默替成程序画。

## 5. 可直接使用的英文提示词

以下各块与对应项目原创导图/遮罩一起使用。替换`{...}`只填写此包/模型已有数值，不让AI自行补新部件。生成结果必须保持实际导图，文字和控制图标后置。

### 所有任务共同前缀

> Create production pixel-art albedo for an ORIGINAL low-poly game asset, using the provided project-owned surface layout and edit mask. Work on the native pixel grid; keep the exact canvas and protected regions. Match the attached project-owned approved material sample in cluster scale and finish, not in subject matter. Use deliberate connected pixel clusters, readable material variation and crisp stepped edges. Preserve the specified geometry boundaries and color families. This is a flat surface texture, not a scene render. Do not invent geometry, panels, text, logos, objects or lights. Do not paint cast shadows from a scene light. No photographic blur, procedural speckle, salt-and-pepper noise, large polygon patches, glossy photoreal PBR or uniformly bright edge outlines. Keep useful detail at the target game camera; do not reduce the result to nearly flat color.

### J01 / M04 不锈钢

> Fine satin SUS304-like stainless steel, cool neutral grey. Base #737F81, subdued bright band #A2ADAA, shadow family #536467 and #37494D. This is a continuous handrail surface unfolded along its length. Suggest restrained longitudinal finish with broad interrupted pixel bands, not many single-pixel scratches. Old handling has subtly smoothed only the marked grip zone; small cool-grey residue is confined to marked bracket and joint contacts. Preserve large intact areas. No orange rust, chrome mirror reflections, fingerprints, wood, soft rubber or painted industrial warning stripes. The tube curvature will be provided by geometry; do not render a cylinder onto the map.

### J02 / M05 涂层金属

> Fine-textured matte powder-coated metal sheet, {LIGHT: base #A7B0AA, shadow #858F8A, light #C1C6BD / DARK: base #4D6065, shadow #36494E, light #718185}. Use only the one specified palette. Render dense, controlled coating texture with grouped low-contrast pixels, not a blank fill. Keep the coating mostly intact. Old contact micro-wear is limited to the guide's lower edge and service contacts; tiny exposed points are grey metal, not bright orange rust. No fabricated seams, screws, rivets, computer circuitry, vents or illuminated outlines. This image is material only; hardware geometry and exact signs are added separately.

### J03-01～03 / M06 普通矿物板，三个独立变体

> Through-colored pale grey mineral facade panel, visually related to fine glass-fibre reinforced concrete, with a dense matte lightly sanded face. Base #B9BDB2, softer shade #969F98, limited light #D0D2C6. Express a coherent fine mineral surface with small connected pixel clusters and broad but restrained tone differences. No large aggregate chips, veins, bricks, tiles, muddy spots, coarse asphalt, random polygon camouflage or structural cracks. Variant {01/02/03} must have genuinely different cluster organization while keeping the same palette and completion level. Follow only the real edge zones in the guide. Do not add repeating borders to edges marked for continuity.

### J03-04 / M06 节点沉积

> Same approved pale grey mineral panel material and palette. Concentrate readable, irregular grouped deposits at the EXACT recessed joint and lower return marked by the guide. Let the deposits break into smaller stepped clusters as they leave the crevice; vary thickness and gaps. Leave most of the main field visibly textured but intact. No complete uniform bright frame, no rectangular dirt sticker, no mid-wall isolated stain, no mold and no damage without a marked origin. This is old sheltered residue, not a broken concrete wall.

### J03-05 / M06 有源雨痕

> Same mineral facade material. Add ONE restrained outdoor runoff history starting precisely at the marked coping or drip joint and fading downward into the existing surface. Use connected stepped pixel clusters and irregular narrowing, not a smooth airbrushed stripe. It should read as material exposure and accumulated residue, not black ink poured on a wall. Keep it local; no second invented source, no algae, salt crust, wide peeling, reinforcement, structural cracks or full-height repeated vertical stains. The guide defines the exterior exposure only; no indoor leakage is implied.

### J04 / M07 锌系金属

> Blue-grey weathered titanium-zinc-like folded cladding, matte patina rather than paint. Base #71858A, folded planes #536970, restrained light #99A7A7, recessed seam #354B52. Follow the original folded-sheet surface layout exactly. The patina is nuanced and coherent across the panel; small surface changes can blend into the tone. Show slight sheltered joint residue and old edge contact, not peeling paint, orange iron rust, heavy corrosion or waviness. No new corrugations, rivets, pipes or fake technological patterns. Keep the material distinct from both mineral panels and brushed steel.

### J05 / 六种门面通用主体＋对应限制

> Refine this exact ORIGINAL {FD-A/FD-B/EL-A/EL-B/EN-A/EN-B} door-front surface guide into authored pixel art. Preserve every leaf boundary, frame, recess, inactive screen mask and release-hardware mask. Use the assigned M05 palette and the supplied approved coating sample. Strengthen material distinction and fine edge construction only where the guide shows real parts. Put restrained old use at the marked lower contact/handle zones and sheltered residue at actual seals. Keep large coated faces intact but not empty. Do not add new bolts, vents, screens, diagonal sci-fi engravings, symbols, lettering, glass windows or glow. Avoid continuous white wear outlines. All indicator colors and CAUTION text are separate runtime elements.

附加约束固定如下，不另选：FD两款无玻璃、保留机械释放区；EL两款所有操作面熄灭且无运行灯；EN外侧允许E3/E4、内侧只E1/E2；所有新门的字与灯图都不在PixelLab这一层生成。

## 6. 资产组装规则

- 每个候选一个命名根节点：`HR_A`、`HR_B`、`FD_A`等；视觉、碰撞、可动门叶、状态窗、发光面分开。GLB保持米制，记录轴向，实际材质使用的UV统一到可导出的UV0；灯光图用独立UV2。
- 材料共享不等于所有贴图共用错误的岛。门片文字不镜像，立面雨痕不任意旋转，不把灯带纵向图拉成另一种像素密度。
- 只影响剪影/遮挡/开合的部分使用真实几何；小涂层破点、接缝细暗边、细拉丝由像素表面完成。扶手、门叶、雨檐必须有真实体积，不能用一张全息平面代替。
- 面向游戏的资产不依赖Blender专用节点。禁止为了让静态图“更像2D”自动换Shader、曝光、镜头或全屏分辨率。
- 所有新烘焙与实际受光执行[光照QA](../ROOM1_LIGHTMAP_QA.md)；纹理UV可重叠不代表光照UV也可重叠。新门/扶手遮挡改变时，不把旧光图贴上去假称已正确受光。
- 立面按模块实例化，不为16层复制大量独立材质；远景简化与近景模块同材质体系。未可见内部不做，先完整交付两套外壳候选。

## 7. 审图页必须让用户能直接比较

### 每组固定输出

| 类别 | 必须画面 |
|---|---|
| 所有材料 | 原生PNG、Nearest 4倍局部、无光色图检查；原图/精修后分别留存 |
| HR-A/B | 同一梯跑正侧/斜向、人物尺度、上下楼方向、最易遮挡处；正常与基础照明 |
| FD-A/B | 同机位闭合、90°打开、两侧状态；释放部件近景；门扫掠/平台净空示意 |
| EL-A/B | 关门无警示、关门有警示、按钮近景、可穿过光条的实际运行；不能出现绿灯 |
| EN-A/B | 同机位室外正面、室内侧、开启、门外过渡；外侧/内侧旧化不一致的证据 |
| FA-A/B | 同视角整体、四向立面、转角、交通节点、首层和屋顶近景；保留尺度参照 |
| ST-01灯带 | 角色接近、行走、停留、转身、离开；20～30秒实际录屏或连续GIF |

构件同组使用相同白平衡、曝光和构图；阴影/材质需同时看中性检查光与实际应急光，不以提高一款亮度“赢得”对比。两款立面用同一临时阴天照明，不声称室外最终天气已定。

### 输出文件和证据

- `preview.md`：GitHub直接内嵌本仓库PNG，先给五组并排A/B，再给细节；不可只链接一个在GitHub上显示源码的HTML。
- `preview.html`：本地可打开的同一内容，路径相对。图片宽度一致，支持原图查看，不把成品压成220px小图。
- `review_manifest.json`：每张图对应候选ID、场景、相机、灯光状态、提交号；标清“技术通过/美术待选/缺项”。
- `source/`含导图、遮罩、参数、原始PixelLab返回与实际用量；`editable/`保留Aseprite原生图层及精修说明；`model/`保留Blender与可复现脚本。
- 验证可移动部件的轴心/碰撞、通路净宽、状态切换、UV/图集、贴图采样和模型导入。检查结果必须与实际图一致，不能仅写一句“全部测试通过”。
- 完成后提交GitHub并读回文件，报告所有候选的状态。用户看最终成果选择；制作端不自动推选一款，也不提前替换正式F5或已冻结Room 1。
