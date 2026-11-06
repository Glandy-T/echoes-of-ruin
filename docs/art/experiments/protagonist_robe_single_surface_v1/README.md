# 已否决：脚本单层白袍重建

状态：`USER_REJECTED_SCRIPT_REBUILD`。用户看到试穿图后指出“？这啥”，随后要求有问题就重新生成。此目录只保留失败记录，不作为角色模型、衣物拓扑或后续绑定的基线。

初版袖截面与轴向不一致，肩部出现尖角，袖子读成扁片；静态零自交不能证明外形合格。后续局部修订没有获得外观认可，本路线已停止。

注意版本边界：`model/robe_single_surface.blend`、GLB 和 `source/garment_build_report.json` 是后续未验收的静态修订；`model/protagonist_fitted.blend`、`source/rig_test_report.json` 和 `evidence/` 是用户否决的较早试穿。两者不是同一版网格的验证组合，不能交叉引用为通过证据。

身体 v2 和原 Tripo 白袍 v2 的认可轮廓保持独立。当前改走 [Tripo v3.1 单独白袍候选](../protagonist_tripo_robe_h31_v1/README.md)，生成后先做原始结构与轮廓检查，不能把生成成功直接当作可动画。
