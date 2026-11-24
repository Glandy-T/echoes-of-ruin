# 主角 R5 行走测试

[带 walk 的原始 GLB](walk.glb) · [正面八帧](walk_f_frames.png) · [右侧八帧](walk_s_frames.png) · [R5 静态原模](../protagonist_smart_mesh_r5/mesh.glb)

国内 [Tripo Studio 的 R5 资产](https://studio.tripo3d.com/workspace/rigging/0f1eafa3-9fbf-487f-9e45-efaa5f741d31)沿用原网格。2K 临时贴图 10 积分，v1.0 类人自动绑定一次 20 积分，选择行走并勾选导出一个动作。余额 1225 → 1215 → 1195。正式贴图尚待 PixelLab 制作。

Blender 回读 8563 个角色三角面、41 骨、walk 动作 0–56 帧。相机跟随角色，正侧每七帧取一张，分别覆盖 0、7、14、21、28、35、42、49 帧。画面用灰色呈现，便于辨认几何变形。

上次静态报告称脚底没有薄板，需要更正。原模第七个连通块的 32 个顶点共面，位于脚底附近。绑定后该块同时受左右脚趾和脚骨驱动，侧面第 2、6 张清楚显示薄片。休眠服下摆随摆臂扬起，侧面第 4、8 张明显。对衣身所在的 1610 顶点连通块检查，归一身高约 0.41 以下有 64 个顶点带超过 5% 的手骨权重。可见裙摆变形已足以退回；这次未做裙面与腿面的逐帧相交检测。

与 R3 同口径测量，排除静止长度不超过 0.002 的边，R5 全动作最大边长比为 2.53（第 35 帧），R3 两次为 7.89、7.47。测试验证动作导出和回读。足底多余网格和下摆权重需要在采用前处理；保留原始结果供复查。

[骨骼与面数](walk_metrics.json) · [逐帧边长](walk_stretch.json) · [各连通块和骨骼权重统计](weighted_parts.json)。review.py、strain.py、weighted_parts.py 通过 Blender 后台运行，-- 后传入 walk.glb；contact.py 拼出正侧帧图。
