# 主角结构 v3：停止继续修补的历史实验

2026-11-06。**未批准、未通过结构验收，不作为当前角色资产。** 保留源工程、改前改后图与诊断，解释为何切换为 Tripo 分件生成。

本轮尝试保留 v2 外形，建立白袍内侧、领口／袖口／下摆收边及独立身体代理。静态开口已有体积，但检查发现源白袍腋下本身存在 54 对非邻面穿插；新内壳与外壳有 116 对相交，身体代理也穿衣。继续补丁会扩大返工，因此遵照用户指示停止手工抢救，改为身体、衣服分别生成。

- 失败检查：[independent_validation.json](source/independent_validation.json)、[具体根因](source/cloth_root_cause.json)。
- 可编辑历史：[Blender](model/protagonist_structure_v3.blend)，包含 BEFORE_V2 与 AFTER_V3；不是可投产模型。
- `uv_trial/` 和棋盘图属于旧试展，**主工程仍未通过 UV 重叠验收**。`prepare_uv_trial.py` 后续局部修复仅在 scratch 测试中成功，不能把测试报告当成此工程已修好。
- 衣服灰模外轮廓后来用于生成项目自有正反面指南；未把有问题的原网格直接当作新衣服交付。
- v1／v2及 Tripo 原始文件没有覆盖；Room1、镜头、光照和游戏角色没有改动。

继续入口：[独立身体与白袍候选](../protagonist_tripo_robe_v2/preview.html)。
