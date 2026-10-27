# 人物动态阴影与休眠舱碰撞 r1 — 2026-10-14，本地待审

用户希望先处理人物动态阴影和休眠舱碰撞；指出当前舱贴图偏精细、像素感减弱，贴图返修留到之后。本轮沿用暗房和连续灯带烘焙r3，没有返修材质或改主场景。

打开 scenes/dev/room1_player_physics_test_r1.tscn，F6运行。WASD／方向键移动；R复位，1～9中央／边缘／四角定位；K切换人物的灯带遮挡阴影，C显示碰撞形状，T隐藏占位体，H说明。L灯带、G舱内光、B屏幕、N光晕沿用。正式人物模型还不存在，目前为1.65m、半径0.22m的胶囊占位体。

## 物理

CharacterBody3D使用move_and_slide，2m/s水平速度、加速度10m/s²、减速14m/s²、重力9.8m/s²；floor_snap_length 0.12、safe_margin 0.001、最大可走坡35°。不新增跳跃、推舱、上舱或门交互。FollowTarget只读取物理人物的位置；摄像机继续固定高度和朝向，不随重力下落上下摆动。

20舱各有一个StaticBody3D及ConvexPolygonShape3D，点集取实际封闭舱的外壳长边／端面／盖板几何，并保留各舱位置和旋转。闭舱作为整体实心障碍，排除内部和玻璃细节，避免窄缝与倒角造成卡点；开盖后的可进入结构未定义。房壳9个网格使用静态三角碰撞，包括地板、左右／前后墙、屋顶与当前关闭的门占位。主角碰撞层2、环境层1，不依靠旧的坐标夹紧阻挡。

## 动态阴影

连续灯带仍是四整条发光面，0个灯带Point/Spot代理。原静态烘焙保留；新接收Shader按人物胶囊实际位置计算接收点到四条灯带的遮挡，各条16个积分样本，得到近似连续面光源的软阴影。只在人物6m范围及相应高度内计算，保留18%的间接反弹底光；不是重新烘焙，也不是贴一个固定黑圆。

这是针对当前胶囊占位体的解析阴影近似，不是正式人物网格的引擎阴影贴图。之后替换人物模型时须同步更新轮廓或换成正式网格方案；动画、衣物、开盖动态遮挡未实现。现有舱内／屏幕局部灯仍可通过Godot原生阴影遮挡人物。占位体的灯带受光也用连续采样近似，强度仅用于当前可读性测试。没有新增均匀房间填光或灯泡状灯带。

## 实际验证

保存9张真实1280×720截图及validation.json：中央人物阴影开／关、后排P12阻挡、前排P02阻挡、沿舱滑行、间隙通过至前墙、左墙阻挡、移动后阴影开／关。

实际物理步进确认：从1m高落地稳定；撞P12停在z≈-6.282，撞P02停在z≈-3.218；斜行沿P02端面滑到x≈4.002；从x=4.4通过约0.7m舱间隙并被前墙挡住；左墙挡在x≈0.421。碰撞查询确认测试位置不与舱体重叠。镜头高度／朝向锁定检查通过，两个不同人物位置的同镜头阴影开关差分均非零。已目视检查中央、移动后和碰舱截图。

技术验证只说明当前占位体方案工作，人物动作手感、阴影观感仍待用户试玩。休眠舱贴图像素感与玻璃接缝列为后续返修。本轮仅本地保存，未提交上传。

源：scripts/dev/room1_player_physics_test_r1.gd、room1_player_shadow_receiver_r1.gdshader、room1_actor_strip_lighting_r1.gdshader、build_room1_player_physics_test_r1.gd、validate_room1_player_physics_test_r1.gd。

API依据：[CharacterBody3D](https://docs.godotengine.org/en/4.6/classes/class_characterbody3d.html)、[ConvexPolygonShape3D](https://docs.godotengine.org/en/4.6/classes/class_convexpolygonshape3d.html)。
