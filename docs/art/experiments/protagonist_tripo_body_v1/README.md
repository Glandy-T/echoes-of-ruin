# 主角独立身体候选 v1

2026-11-06。国内版 Tripo P2.0，一次私有文字生成；身体与衣服分开，为后续换装保留基础。

入口：[身体／白袍多角度对照](../protagonist_tripo_robe_v2/preview.html) · [Blender 检查工程](model/protagonist_body_v1_inspection.blend) · [原始 GLB](model/protagonist_tripo_body_v1_raw.glb) · [四边面 OBJ](model/protagonist_tripo_body_v1_raw.obj)。

身体是中性灰色人体候选，当前不是最终脸部或肤色设计。没有头发、衣物、UV、骨架和权重；原始模型及 AIGC 标记原样保留。[提示词](source/prompt.txt)、[生成记录](source/generation_record.json)、[导入统计](source/mesh_audit.json)可追溯。网页的 3402 面包含 2728 四边面和 674 三角面；GLB 为 6130 三角面。OBJ 的大量小连通片来自重复顶点，不能解释为身体零件数量。

**静态检查尚未通过：**GLB为单连通闭合体、无非流形边和退化面，但[独立精确检查](source/body_topology_check.json)发现两脚趾附近共28对非邻面真正相交，必须先局部简化。未在腋下、躯干和手指高度检测到同类交叉，不代表动作测试通过。网页局部重试界面曾打开，但未提交任何重试。

身体的实际 A 姿势与衣服并不完全一致；需统一休止姿势、身高和关节，再试穿／绑骨。不得直接把当前归一化高度当成最终米制身高。

费用边界：提交前显示 P2.0 Trial×1、价格0；余额跨观察3300→3245→3190，同时账户还有其他工作，无法确认每一步实际计费；不可写成已证实的单次110额度。
