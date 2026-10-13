# 主角衣发素材候选与制作方向

2026-10-13。候选已看作者实物预览，尚未购买或下载源模型，也未被用户批准。

## 当前决定

用户否定了自建头发的外观，要求除建筑外优先寻找现成素材，再做适配修改。
停止 `player_character_v3` 的自建衣发路线；该目录的造型、贴图和预览均不作为批准资产。
此前用户认可的 pistachio 人体基模可保留，独立进行 UV 与骨架验证。

角色要求仍是：165 cm、自然比例、长发、白色长衣、赤脚，无绘制五官但保留面部体积。
身体、头发、衣服保持独立可编辑网格和 UV。先确认静态外观，再处理动作与最终像素贴图。

## 当前候选

### 长发优先候选：female stylised hair lowpoly（免费）

- 作者：Asam-mk。
- [作者商品页](https://www.cgtrader.com/free-3d-models/character/woman/female-stylised-hair-lowpoly)。
- [实际预览](https://img-new.cgtrader.com/items/5976740/8e7b3b2e6b/female-stylised-hair-lowpoly-3d-model-8e7b3b2e6b.webp)。
- 页面标为免费，提供 Blender、FBX、OBJ；许可标签为 Royalty Free License (no AI)，不是 CC0。
- 实际预览上排第三款为露额头与面部的较长发型，有明确发束和侧面起伏。
  相比下面的写实发片，几何发束更接近当前希望的简化体积，但须延长、减弱发尾卷曲并适配头型。
- 页面描述称十款，首张图显示八款；准确包含数量未下载复核。
- 页面技术区同时出现平台的 No UV overlaps 和作者填写的 Overlapping，UV 状态矛盾，需查源文件。
- 作者写约 1,000 面，实际各款面数、骨架和权重均待导入验证。

### 长发备选：Female Long Straight Hair FREE

- 作者：hamza khaloui。
- [作者商品页](https://www.artstation.com/marketplace/p/bjlDX/female-long-straight-hair-free)。
- [实际预览](https://cdna.artstation.com/p/marketplace/presentation_assets/003/092/948/large/file.jpg?1697019469)。
- 本次页面价格 **USD 1**；标题中的 FREE 与实际标价不一致。
- 预览中为长直发、侧向刘海，脸部可见，可作为发型轮廓候选。
- 作者称为模块化 hair cards，提供 Blender、FBX、OBJ、纹理等文件。
- 当前素材偏写实；需调整发长、刘海与侧面轮廓，简化细丝感并适配像素材质。
- 面数、骨架、权重、透明边缘在 Godot 中的表现：**未下载验证，TBD**。

### 白色长衫：Low Poly Medieval Female - Linen Chemise

- 作者：Tatiana Smith。
- [作者商品页](https://www.artstation.com/marketplace/p/epppn/low-poly-medieval-female-linen-chemise-game-ready-npc-clothing-unreal-unity)。
- [实际预览](https://cdnb.artstation.com/p/marketplace/presentation_assets/005/261/725/large/file.jpg?1774581643)。
- 本次页面价格 **USD 5**。
- 预览为浅色、长袖、长下摆服装；需要去掉下摆花边，按原角色调整衣长、领口与宽松度。
- 作者提供手工重拓扑 FBX、Marvelous Designer ZPRJ 和纹理。
- 页面两处面数分别为 1,034 与 1,010，故仅记为约一千面，准确值待导入。
- 作者声明 UV 不重叠、真实尺度、Weight Map；这些属于页面声明，尚未实际复核。
- Weight Map 不等于已确认可直接使用的完整骨架绑定。身体不包含在商品内。

## 许可与交付范围

两件 ArtStation 商品页面当前均标为 Standard Use License：个人使用及一个商业项目，
页面列出最多 2,000 次销售或 20,000 次浏览。最终采购时须核对当时完整许可及项目适用范围。
免费 CGTrader 发型包的完整许可及具体允许的分发形式尚未核对，暂作为外观候选。
当前只保存来源与选择依据，没有购买、下载或提交这些候选商品的模型及贴图。
若以后采用，公开 GitHub 只提交许可允许分发的成果；不默认公开付费源素材。

## 下一轮验证

1. 用户选定衣发外观后再取得源文件，并确认源文件和许可。
2. 先验证独立网格、UV、法线、尺度和实际面数，再适配到 165 cm 基模。
3. 保持脸部与颈肩轮廓可读，检查正面、侧面及游戏镜头，不仅看商品正面图。
4. 处理白袍下摆、袖口与头发的绑定；以屈肘、迈步、蹲下诊断穿插与变形。
5. 制作像素材质并在游戏目标镜头检查。像素密度尚未冻结，不直接继承商品的 4K 材质。

人体的权重修复和已知 UV 问题见 `assets/characters/work/player_basemesh_v2_1/README.md`。
