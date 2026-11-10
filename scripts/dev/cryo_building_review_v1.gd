extends Node3D
## Isolated asset review. No inherited routes, gameplay permissions, or baked lighting.
const ROOT := "res://assets/art/cryo_building_review_v1/"
const OUT := "res://docs/art/experiments/cryo_building_review_v1/evidence/godot/"
const VIEW := Vector2i(1280,720)
const IDS := ["HR-A","HR-B","FD-A","FD-B","EL-A","EL-B","EN-A","EN-B","FA-A","FA-B"]
const WAYPOINTS := [Vector3(-3.60,0,0),Vector3(-1.65,0,0),Vector3(1.65,1.90,0),Vector3(2.62,1.90,0),Vector3(2.62,1.90,-2),Vector3(1.65,1.90,-2),Vector3(-1.65,3.80,-2),Vector3(-3.25,3.80,-2)]
const COLOR := {"M01":"d3d6c9","M02":"5a6c73","M03":"7c8380","M04":"737f81","M05-L":"a7b0aa","M05-D":"4d6065","M06":"b9bdb2","M07":"71858a","M08":"263b3e","M09":"8f9d99","M10":"4e5b5b"}
var stage: Node3D
var camera: Camera3D
var world: Environment
var sun: DirectionalLight3D
var actor: Sprite3D
var hud: Label
var notice: Label
var candidate := "HR-A"
var shot_label := ""
var view_name := "hero"
var lights: Array[Array] = []
var diffusers: Array[Array] = []
var lit: Array[float] = [.20,.20,.20,.20]
var hold: Array[float] = [0.,0.,0.,0.]
var state_fault := false
var opened := false
var capture_running := false
var motion_running := true
var motion_t := 0.
var banner_t := 0.
var banner_text: Array[Label] = []
var banner: MeshInstance3D
var banner_cycle := 1.
var door_pivots: Array[Node3D] = []
var shots: Array[Dictionary] = []
var missing: Dictionary = {}
var material_cache: Dictionary = {}
var assertion_log: Array[Dictionary] = []
var body_bounds := {}
var choice := 0
var stair_environment := true
var _zone_before := -1
var _path_before := 0.

func _ready() -> void:
	get_window().size = VIEW
	var env_node := WorldEnvironment.new()
	world = Environment.new(); world.background_mode = Environment.BG_COLOR; world.background_color = Color("39484c")
	world.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; world.ambient_light_color = Color("e3e9e6")
	world.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env_node.environment = world; add_child(env_node)
	sun = DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-43,-29,0); sun.light_color = Color("f2f4ed")
	sun.shadow_enabled = true; sun.directional_shadow_max_distance = 300.; add_child(sun)
	camera = Camera3D.new(); camera.projection = Camera3D.PROJECTION_ORTHOGONAL; camera.near=.04; camera.far=900.; camera.current=true; add_child(camera)
	var ui := CanvasLayer.new(); add_child(ui)
	hud = Label.new(); hud.position = Vector2(24,18); hud.add_theme_font_size_override("font_size",22); ui.add_child(hud)
	notice = Label.new(); notice.position = Vector2(24,676); notice.add_theme_font_size_override("font_size",15); ui.add_child(notice)
	for label:Label in [hud,notice]:
		label.add_theme_color_override("font_outline_color",Color("203033")); label.add_theme_constant_override("outline_size",6)
	var mode := OS.get_cmdline_user_args()
	if mode.has("--capture"): call_deferred("capture_all")
	else: show_variant("HR-A")

func _png(name: String) -> Texture2D:
	var path := ROOT+"textures/"+name+".png"
	if ResourceLoader.exists(path): return load(path) as Texture2D
	# Runtime can load only this review set's native source PNGs prior to editor import.
	if FileAccess.file_exists(path):
		var im := Image.load_from_file(ProjectSettings.globalize_path(path))
		if im and not im.is_empty():
			im.generate_mipmaps(); return ImageTexture.create_from_image(im)
	return null

func mat(name: String, distant := false) -> StandardMaterial3D:
	var key := name+str(distant)
	if material_cache.has(key): return material_cache[key] as StandardMaterial3D
	var m := StandardMaterial3D.new(); m.resource_name=name
	m.roughness=.88; m.metallic_specular=.12; m.metallic=.0
	if name=="M04": m.metallic=.35; m.roughness=.75
	if name=="M07": m.roughness=.8
	var tex_name := "M06-01" if name=="M06" else "M06-02" if name=="M06-BASE" else name
	var tex := _png(tex_name)
	m.texture_filter=BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS if distant else BaseMaterial3D.TEXTURE_FILTER_NEAREST
	m.texture_repeat=name!="M06-R" and not name.begins_with("FACE_")
	if tex:
		m.albedo_texture=tex
		if name=="M06-BASE":m.albedo_color=Color("b8c0bc")
		if name=="M08":m.albedo_color=Color("596a6d")
	else:
		missing[tex_name]=true
		var base := name if COLOR.has(name) else "M06" if name.begins_with("M06") else "M05-D" if name.begins_with("FACE_EL") or name=="FACE_EN_B" else "M05-L"
		m.albedo_color=Color(COLOR[base])
	material_cache[key]=m;return m

func import_asset(file: String, distant:=false) -> Node3D:
	var packed := load(ROOT+"models/"+file+".glb") as PackedScene
	assert(packed,"Missing review model "+file)
	var model := packed.instantiate() as Node3D; stage.add_child(model)
	for nn in model.find_children("*","MeshInstance3D",true,false):
		var n := nn as MeshInstance3D
		for i in n.mesh.get_surface_count():
			var source := n.get_active_material(i)
			if source:
				var surface:=mat(source.resource_name,distant)
				if "DarkTouch" in str(n.name):
					surface=surface.duplicate() as StandardMaterial3D
					surface.albedo_color=Color("27393e")
					surface.metallic_specular=.0
				if "DirectionLight" in str(n.name):
					surface=surface.duplicate() as StandardMaterial3D
					surface.emission_enabled=true;surface.emission=Color("dce7e4");surface.emission_energy_multiplier=.18
				n.set_surface_override_material(i,surface)
	return model

func box(name: String, center: Vector3, size: Vector3, material_name: String, use_texture:=true) -> MeshInstance3D:
	var o := MeshInstance3D.new();o.name=name;o.position=center
	var m: StandardMaterial3D
	if use_texture:
		m=mat(material_name).duplicate() as StandardMaterial3D
	else:
		m=StandardMaterial3D.new();m.albedo_color=Color(COLOR.get(material_name,"626b69"));m.roughness=1.;m.metallic_specular=0.
	var hw:=size*.5;var q: Array[Vector3]=[Vector3(-hw.x,-hw.y,-hw.z),Vector3(hw.x,-hw.y,-hw.z),Vector3(hw.x,-hw.y,hw.z),Vector3(-hw.x,-hw.y,hw.z),Vector3(-hw.x,hw.y,-hw.z),Vector3(hw.x,hw.y,-hw.z),Vector3(hw.x,hw.y,hw.z),Vector3(-hw.x,hw.y,hw.z)]
	var facets := [[0,1,2,3],[4,7,6,5],[3,2,6,7],[1,0,4,5],[2,1,5,6],[0,3,7,4]]
	var normals := [Vector3.DOWN,Vector3.UP,Vector3.BACK,Vector3.FORWARD,Vector3.RIGHT,Vector3.LEFT]
	var tool:=SurfaceTool.new();tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	var tex := m.albedo_texture; var px:=Vector2(80./tex.get_width(),80./tex.get_height()) if tex else Vector2.ONE
	for j in 6:
		var normal:Vector3=normals[j]
		for i in [0,2,1,0,3,2]:
			var p:=q[facets[j][i]];var w:=p+center
			var uv:=Vector2(w.x,-w.z) if j<2 else Vector2(w.x,-w.y) if j<4 else Vector2(w.z,-w.y)
			tool.set_normal(normal);tool.set_uv(uv*px);tool.add_vertex(p)
	o.mesh=tool.commit();o.material_override=m;stage.add_child(o);return o

func reset_stage(id: String) -> void:
	if is_instance_valid(stage): remove_child(stage);stage.queue_free()
	stage=Node3D.new();stage.name="IndependentReviewSet";add_child(stage)
	candidate=id;actor=null;banner=null;door_pivots.clear();lights.clear();diffusers.clear();banner_text.clear();missing.clear();material_cache.clear()
	motion_t=0.;banner_t=0.;opened=false;state_fault=false;stair_environment=id.begins_with("HR") or id=="ST-01"
	_zone_before=-1;_path_before=0.;lit=[.20,.20,.20,.20];hold=[0.,0.,0.,0.]

func show_variant(id: String) -> void:
	reset_stage(id)
	var outside := id.begins_with("FA") or id.begins_with("EN")
	world.background_color=Color("68777a") if outside else Color("343e42")
	world.ambient_light_energy=.60 if outside else .46
	sun.light_energy=.40 if outside else .52
	sun.shadow_enabled=not outside
	if not outside and not stair_environment:
		world.ambient_light_energy=.30
		sun.light_energy=.28
	if stair_environment:
		var base := import_asset("ST-01_stair_sample")
		if id.begins_with("HR"): import_asset(id)
		setup_stair_lights(base)
		setup_actor()
		var signboard:=box("K01_LevelSign",Vector3(3.425,3.55,-.65),Vector3(.02,.18,.30),"M05-D")
		place_label(signboard.position+Vector3(-.012,0,0),-90.,"4F",.009)
		set_view("hero")
	elif id.begins_with("FA"):
		import_asset(id+"_complete_envelope",true)
		import_asset("EXTERIOR_K01_common",true)
		box("ReviewGround",Vector3(0,-.12,0),Vector3(580,.20,500),"M03",false)
		setup_actor();actor.position=Vector3(18,.80,40.1)
		set_view("overall")
	else:
		var model := import_asset(id)
		var w := 1.4 if id.begins_with("EL") else 1.8
		var gap := w*.5
		box("WallLeft",Vector3(-(gap+3.0)/2,1.45,-.16),Vector3(3.0-gap,2.90,.30),"M06" if outside else "M01")
		box("WallRight",Vector3((gap+3.0)/2,1.45,-.16),Vector3(3.0-gap,2.90,.30),"M06" if outside else "M01")
		box("WallHead",Vector3(0,2.65,-.16),Vector3(gap*2,.50,.30),"M06" if outside else "M01")
		box("ReviewFloor",Vector3(0,-.058,0),Vector3(6,.10,7.0),"M06" if outside else "M02")
		for p in model.find_children("*PIVOT","Node3D",true,false): door_pivots.append(p as Node3D)
		for n in model.find_children("*Leaf_*","MeshInstance3D",true,false): (n as MeshInstance3D).create_trimesh_collision()
		if id.begins_with("EL"): setup_caution(w,id)
		if id.begins_with("EN"):
			box("K01_ExitSign",Vector3(0,2.73,-.328),Vector3(.36,.12,.025),"M05-D")
			place_label(Vector3(0,2.73,-.342),180.,"出口 / EXIT",.0054)
		set_view("front")
	hud.text="标准休眠楼   /   "+id
	notice.text=("ASSET ONLY / 首层室外锚点未确认   ·   " if id.begins_with("EN") else "")+"1–0 候选   ↑↓ 视角   O 开闭   C 警示   L 灯光"
	if not missing.is_empty(): notice.text+="   |   缺图： "+", ".join(missing.keys())
	if id.begins_with("HR"):notice.text+="   |   净宽约 1.62 m：独立样段，暂不安装"

func place_label(p:Vector3,ry:float,label_text:String,pixel:float) -> void:
	var l:=Label3D.new();var f:=SystemFont.new();f.font_names=PackedStringArray(["Yu Gothic UI","MS Gothic","Noto Sans CJK JP"])
	l.font=f;l.font_size=16;l.pixel_size=pixel;l.text=label_text;l.outline_size=0;l.modulate=Color("dce7e4");l.position=p;l.rotation_degrees.y=ry;stage.add_child(l)

func setup_actor() -> void:
	actor=Sprite3D.new();actor.name="ExistingSpriteScaleReference"
	var tx := AtlasTexture.new();tx.atlas=load("res://assets/characters/idle.png") as Texture2D;tx.region=Rect2(0,0,96,128);tx.filter_clip=true
	actor.texture=tx;actor.pixel_size=.016;actor.texture_filter=BaseMaterial3D.TEXTURE_FILTER_NEAREST
	actor.billboard=BaseMaterial3D.BILLBOARD_ENABLED;actor.shaded=true;actor.alpha_cut=SpriteBase3D.ALPHA_CUT_DISCARD;actor.position=Vector3(-3.3,.91,0)
	stage.add_child(actor)

func setup_stair_lights(root: Node3D) -> void:
	var names := [["L01_ZONE_LOWER"],["L01_ZONE_TURN","L01_TURN_BACK","L01_TURN_UPPER_RETURN"],["L01_ZONE_UPPER"],["L01_ZONE_FLOOR"]]
	for i in 4:
		var emitters: Array[StandardMaterial3D]=[]
		for object_name:String in names[i]:
			var node := root.find_child(object_name,true,false) as MeshInstance3D
			if node:
				for si in node.mesh.get_surface_count():
					var m := mat("M09").duplicate() as StandardMaterial3D;m.emission_enabled=true;m.emission=Color("dce7e4");m.emission_energy_multiplier=.20
					node.set_surface_override_material(si,m);emitters.append(m)
		diffusers.append(emitters)
	var positions := [[Vector3(-.9,1.65,.63),Vector3(.64,2.51,.63)],[Vector3(2.66,2.89,.48),Vector3(2.7,2.89,-1.75)],[Vector3(.67,3.58,-2.65),Vector3(-.86,4.45,-2.65)],[Vector3(-2.55,4.82,-2.65)]]
	for ii in 4:
		var bank: Array[OmniLight3D]=[]
		for p: Vector3 in positions[ii]:
			var l:=OmniLight3D.new();l.position=p;l.light_color=Color("dce7e4");l.omni_range=2.75;l.omni_attenuation=1.6;l.light_energy=.20*.68;l.shadow_enabled=true;stage.add_child(l);bank.append(l)
		lights.append(bank)

func setup_caution(w: float, id: String) -> void:
	var sv:=SubViewport.new();sv.size=Vector2i(832,100);sv.transparent_bg=true;sv.render_target_update_mode=SubViewport.UPDATE_ALWAYS;stage.add_child(sv)
	var bg:=ColorRect.new();bg.position=Vector2(0,17);bg.size=Vector2(832,66);bg.color=Color(.19,.136,.045,.56);sv.add_child(bg)
	for y in [18,80]:
		var r:=ColorRect.new();r.position=Vector2(0,y);r.size=Vector2(832,2);r.color=Color(.79,.66,.36,.62);sv.add_child(r)
	var font:=SystemFont.new();font.font_names=PackedStringArray(["Yu Gothic UI","MS Gothic","Noto Sans CJK JP"])
	for i in 2:
		var label:=Label.new();label.text="CAUTION — 電力不足により運転停止中。階段をご利用ください。";label.add_theme_font_override("font",font);label.add_theme_font_size_override("font_size",36);label.modulate=Color("c9a85b");label.position.y=25
		sv.add_child(label);banner_text.append(label)
	banner_cycle=maxf(860.,font.get_string_size(banner_text[0].text,HORIZONTAL_ALIGNMENT_LEFT,-1,36).x+85.)
	banner=MeshInstance3D.new();banner.name="CautionVisualOnly_NoCollision"
	var q:=QuadMesh.new();q.size=Vector2(w+.10,.18);banner.mesh=q
	banner.position=Vector3(0,1.10,.12)
	var sm:=StandardMaterial3D.new();sm.albedo_texture=sv.get_texture();sm.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
	sm.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;sm.cull_mode=BaseMaterial3D.CULL_DISABLED;sm.depth_draw_mode=BaseMaterial3D.DEPTH_DRAW_DISABLED
	banner.material_override=sm;stage.add_child(banner)
	body_bounds[id]=w

func set_view(v: String) -> void:
	view_name=v
	var p:=Vector3(0,1.6,5);var target:=Vector3(0,1.38,0);var s:=3.45
	if candidate.begins_with("FA"):
		for n in stage.find_children("TECHNICAL_B4_B1_ASSEMBLY*","MeshInstance3D",true,false): n.visible=v=="b4"
		p=Vector3(151,103,146);target=Vector3(0,30,0);s=135.
		match v:
			"north": p=Vector3(0,29,-240);target=Vector3(0,29,0);s=121.
			"south": p=Vector3(0,29,240);target=Vector3(0,29,0);s=121.
			"west": p=Vector3(-230,30,0);target=Vector3(0,30,0);s=72.
			"east": p=Vector3(230,30,0);target=Vector3(0,30,0);s=72.
			"detail10m": p=Vector3(16,8,48);target=Vector3(16,8,38.9);s=5.625
			"corner": p=Vector3(103,16,49);target=Vector3(92,13,37);s=19.
			"node": p=Vector3(106,27,31);target=Vector3(95,26,23);s=16.
			"ground": p=Vector3(22,3.5,53);target=Vector3(19,2.1,38.9);s=6.7
			"roof": p=Vector3(103,72,46);target=Vector3(91,60.8,34);s=18.
			"b4": p=Vector3(125,7,116);target=Vector3(0,7,0);s=95.
	elif stair_environment:
		p=Vector3(-7.1,5.9,-1.45);target=Vector3(.45,2.50,-1.0);s=7.65
		for wall_pattern:String in ["L01_ZONE_UPPER*","L01_ZONE_FLOOR*","L01_TURN_UPPER_RETURN*"]:
			for wall in stage.find_children(wall_pattern,"MeshInstance3D",true,false):
				wall.visible=v!="rail"
		match v:
			"side": p=Vector3(-4.9,2.25,-.7);target=Vector3(1.6,1.65,-.58);s=3.5
			"upper": p=Vector3(-4.6,4.9,-2.3);target=Vector3(2.3,2.70,-1.93);s=4.5
			"landing": p=Vector3(1.3,3.4,-1.3);target=Vector3(2.6,2.15,-1.35);s=2.9
			"rail": p=Vector3(-.27,6.685,-4.61);target=Vector3(.78,1.96,-.51);s=3.0
	else:
		match v:
			"rear": p=Vector3(0,1.6,-5);target=Vector3(0,1.38,0)
			"release": p=Vector3(.68,1.52,-3.2);target=Vector3(.11,1.06,-.03);s=1.50
			"open90": p=Vector3(2.8,2.4,4.5);target=Vector3(0,1.28,.18);s=3.50
			"touch": p=Vector3(1.9,1.62,3.7);target=Vector3(.70,1.19,0);s=1.5
			"transition": p=Vector3(2.8,2.8,4.2);target=Vector3(0,1.25,.48);s=3.75
			"sweep": p=Vector3(0,7.0,1.4);target=Vector3(0,.3,0);s=3.5
	camera.size=s;camera.position=p;camera.look_at(target,Vector3.UP)

func set_door(open: bool) -> void:
	opened=open
	for p in door_pivots:
		var sign_value := -1. if p.name.contains("01") else 1.
		p.rotation.y=sign_value*PI/2. if open else 0.

func _actor_pos(d: float) -> Vector3:
	var remaining:=maxf(0.,d)
	for i in WAYPOINTS.size()-1:
		var a:Vector3=WAYPOINTS[i];var b:Vector3=WAYPOINTS[i+1];var span:=Vector2(a.x-b.x,a.z-b.z).length()
		if remaining<=span: return a.lerp(b,remaining/span)
		remaining-=span
	return WAYPOINTS.back()

func _distance(t: float) -> float:
	if t<6.0: return -.9+t*1.13
	if t<8.8: return 5.88
	if t<11.0: return 5.88-(t-8.8)*.66
	if t<21.0: return 4.428+(t-11.)*1.25
	return 16.928+(t-21.)*1.27

func stair_state(t: float, dt: float, neutral := false) -> void:
	if not is_instance_valid(actor) or lights.is_empty(): return
	var d:=_distance(t);var p:=_actor_pos(d)
	if p.x>=-1.65 and p.x<1.65:
		if is_zero_approx(p.z): p.y=clampf(floorf((p.x+1.65)/.30)+1.,1.,11.)*(1.9/12.)
		if is_equal_approx(p.z,-2.): p.y=1.9+clampf(floorf((1.65-p.x)/.30)+1.,1.,11.)*(1.9/12.)
	actor.visible=d>=0. and d<=15.1
	actor.position=p+Vector3(0,.93,0)
	var zone:=0 if d<5.25 else 1 if d<9.19 else 2 if d<12.49 else 3
	var a:=_distance(t-.06);var dir:=signf(d-a)
	var next:=clampi(zone+int(dir),0,3)
	var boundary:float=[5.25,9.19,12.49,14.1][zone] if dir>=0 else [0.,5.25,9.19,12.49][zone]
	for i in 4:
		var occupancy:=d>=0. and d<=15.1 and i==zone
		var approach: bool=(d>=-1.5 and d<0. and i==0) or (d>=0. and d<=15.1 and i==next and absf(d-boundary)<=1.5)
		var paused_neighbors: bool=d>=0. and d<=15.1 and dir==0. and absi(i-zone)<=1
		if (occupancy or approach or paused_neighbors) and not state_fault: hold[i]=6.
		else: hold[i]=maxf(0.,hold[i]-dt)
		var active:=hold[i]>0. and not state_fault
		lit[i]=move_toward(lit[i],1. if active else .20,dt*(2. if active else .80/1.5))
		for light:OmniLight3D in lights[i]:light.light_energy=.68*lit[i]
		for em:StandardMaterial3D in diffusers[i]:em.emission_energy_multiplier=.45*lit[i]
	if neutral: world.ambient_light_energy=.38;sun.light_energy=.27
	else: world.ambient_light_energy=.19;sun.light_energy=.20
	_zone_before=zone;_path_before=d

func _process(delta: float) -> void:
	if not capture_running:
		banner_t+=delta;update_banner()
		if stair_environment and motion_running:
			motion_t=fmod(motion_t+delta,26.);stair_state(motion_t,delta)

func update_banner() -> void:
	if banner_text.is_empty(): return
	var w:float=body_bounds[candidate]+.10
	var x:float=28.-fmod(banner_t*.22*832./w,banner_cycle)
	for i in 2:banner_text[i].position.x=x+i*banner_cycle

func _unhandled_key_input(event: InputEvent) -> void:
	if capture_running or not event is InputEventKey or not event.pressed or event.echo:return
	var k: int=event.keycode
	if k>=KEY_1 and k<=KEY_9:choice=k-KEY_1;show_variant(IDS[choice])
	if k==KEY_0:choice=9;show_variant(IDS[choice])
	if k==KEY_O and not door_pivots.is_empty():set_door(not opened)
	if k==KEY_C and is_instance_valid(banner):banner.visible=not banner.visible
	if k==KEY_L:state_fault=not state_fault
	if k in [KEY_UP,KEY_DOWN]:
		var vs:= ["hero","side","upper","landing","rail"] if stair_environment else ["overall","north","south","west","east","detail10m","node","ground","roof","b4"] if candidate.begins_with("FA") else ["front","rear","release","open90","transition","touch"]
		set_view(vs[posmod(vs.find(view_name)+(1 if k==KEY_UP else -1),vs.size())])

func capture(name: String, view: String, state: String) -> void:
	set_view(view)
	for i in 3: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var im:=get_viewport().get_texture().get_image();assert(im.get_size()==VIEW)
	assert(im.save_png(OUT+name+".png")==OK)
	shots.append({"file":name+".png","candidate":candidate,"view":view,"state":state,"resolution":[1280,720],"camera":str(camera.global_transform),"ortho_m":camera.size,"missing_textures":missing.keys(),"rt_light_energy":sun.light_energy,"zone_factors":lit.duplicate(),"static_bake":"none"})

func capture_all() -> void:
	capture_running=true;motion_running=false
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for id: String in IDS:
		show_variant(id);var n:=id.to_lower()
		if id.begins_with("HR"):
			state_fault=true;stair_state(3.1,2.0);await capture(n+"_baseline","hero","minimum_0.2_fault_demo")
			state_fault=false;stair_state(3.1,2.0);await capture(n+"_occupied","hero","occupied")
			await capture(n+"_side","side","lower_game_direction")
			await capture(n+"_upper","upper","upper_game_direction")
			stair_state(3.1,1.,true);await capture(n+"_neutral","hero","neutral_surface_review")
			actor.visible=false
			await capture(n+"_rail","rail","guard_profile_and_grip")
		elif id.begins_with("FA"):
			for v: String in ["overall","north","south","east","west","detail10m","corner","node","ground","roof"]:await capture(n+"_"+v,v,"shared_overcast")
			stage.get_node("ReviewGround").visible=false;await capture(n+"_b4","b4","technical_underground_view")
		elif id.begins_with("EL"):
			banner.visible=false;await capture(n+"_closed","front","unpowered_no_caution")
			banner.visible=true;banner_t=.4;update_banner();await capture(n+"_caution","front","unpowered_caution")
			await capture(n+"_touch","touch","dark_call_module")
			await get_tree().physics_frame;await get_tree().physics_frame
			var query:=PhysicsRayQueryParameters3D.create(Vector3(-.18,1.1,.32),Vector3(-.18,1.1,.045));var short:=get_world_3d().direct_space_state.intersect_ray(query)
			query.to=Vector3(-.18,1.1,-.23);var long_hit:=get_world_3d().direct_space_state.intersect_ray(query)
			var probe:=CharacterBody3D.new();probe.position=Vector3(-.20,.87,.38);probe.collision_layer=0
			var col:=CollisionShape3D.new();var cap:=CapsuleShape3D.new();cap.radius=.125;cap.height=1.62;col.shape=cap;probe.add_child(col);stage.add_child(probe)
			await get_tree().physics_frame;await get_tree().physics_frame
			var pass_panel:=probe.move_and_collide(Vector3(0,0,-.29))
			var stop_door:=probe.move_and_collide(Vector3(0,0,-.38))
			assertion_log.append({"candidate":id,"caution_visual_ray_passes":short.is_empty(),"closed_leaf_blocks":not long_hit.is_empty(),"capsule_crosses_caution":pass_panel==null,"capsule_stops_at_closed_leaf":stop_door!=null,"auth_or_operation":false})
			setup_actor();actor.position=probe.position;await capture(n+"_pass","front","capsule_passes_display_stops_at_door")
		else:
			await capture(n+"_closed","front","closed")
			await get_tree().physics_frame;await get_tree().physics_frame
			var door_ray:=PhysicsRayQueryParameters3D.create(Vector3(.22,1.25,.83),Vector3(.22,1.25,-.85))
			var closed_hit:=get_world_3d().direct_space_state.intersect_ray(door_ray)
			await capture(n+"_rear","rear","closed_inner")
			await capture(n+"_release","release","mechanical_release")
			set_door(true);await capture(n+"_open90","open90","two_leaves_at_90")
			await capture(n+"_sweep","sweep","open_leaf_clearance_technical")
			await get_tree().physics_frame;await get_tree().physics_frame
			var open_hit:=get_world_3d().direct_space_state.intersect_ray(door_ray)
			assertion_log.append({"candidate":id,"closed_leaf_blocks":not closed_hit.is_empty(),"open_center_ray_clear":open_hit.is_empty(),"hinge_count":door_pivots.size(),"placement":"isolated_review_no_frozen_landing_sweep_claim"})
			if id.begins_with("EN"): await capture(n+"_transition","transition","asset_only_exterior_transition")
			set_door(false)
	show_variant("ST-01");stair_state(3.1,2.0);await capture("st-01_whole","hero","two_flight_shared_sample")
	show_variant("HR-A")
	for f in 112:
		stair_state(float(f)*.25,.25);await capture("stair_motion_%03d"%f,"hero","deterministic_28s_motion")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(shots,"\t"))
	FileAccess.open(OUT+"runtime_probes.json",FileAccess.WRITE).store_string(JSON.stringify(assertion_log,"\t"))
	print("CRYO_REVIEW_CAPTURE_COMPLETE ",shots.size());get_tree().quit()
