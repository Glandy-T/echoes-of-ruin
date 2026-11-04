extends "res://scripts/dev/cryo_4f_complete_v3.gd"

const CONTEXT_V6 := preload("res://scripts/dev/cryo_4f_camera_context_v6.gdshader")
const SECTION_V6 := preload("res://scripts/dev/cryo_4f_camera_section_v6.gdshader")
const CAMERA_CASES := [
	{"id":"A","name":"原构图","distance":8.0,"fov":50.0},
	{"id":"B","name":"镜头前移","distance":6.0,"fov":50.0},
	{"id":"C","name":"缩小视角","distance":8.0,"fov":38.5},
	{"id":"D","name":"适度组合","distance":7.0,"fov":44.0},
	{"id":"E","name":"更近构图","distance":4.0,"fov":50.0},
]
const REVEAL_LEVELS := [.5,1.0]
const ENTER_DISTANCE := 1.15
const EXIT_DISTANCE := 1.35
const REGION_ENTER_HALF_WIDTH := 1.2
const REGION_EXIT_HALF_WIDTH := 1.5
const RELEASE_HOLD_SECONDS := .20
const FADE_SECONDS := .28
var comparison_ready := false
var comparison_updating_camera := false
var camera_case := 0
var trigger_case := 0 # 0: distance along the whole room facade; 1: door-front region.
var reveal_level_index := 0
var wall_override := 0 # 0 automatic, 1 forced hidden, 2 forced revealed.
var active_corridor := -1
var front_planes: Array[float]=[]
var context_materials: Array[ShaderMaterial]=[]
var reveal_sections: Dictionary={}
var reveal_events: Array[Dictionary]=[]
var comparison_time := 0.0
var room_camera_fov := 50.0
var applied_corridor := -999

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():return
	room_camera_fov=$ReviewCamera.fov
	for i in 8:front_planes.append(4.2-float(floor_layout.walk_rects[i][3])-.1)
	_install_context_materials()
	_build_reveal_sections()
	comparison_ready=true
	update_follow_camera();_update_info()

func _install_context_materials() -> void:
	for entry in occluders:
		var mesh := entry.mesh as MeshInstance3D
		if not corridor_sample.is_ancestor_of(mesh):continue
		var original: Material=entry.originals[0]
		var material: ShaderMaterial
		if original is ShaderMaterial:
			material=original
			var parameters := {}
			for key in ["color_map","emission_map","irradiance_map","is_wall","lamp_power","baked_energy"]:parameters[key]=material.get_shader_parameter(key)
			material.shader=CONTEXT_V6
			for key in parameters:material.set_shader_parameter(key,parameters[key])
		else:
			material=ShaderMaterial.new();material.shader=CONTEXT_V6
			material.set_shader_parameter("plain_surface",true)
			material.set_shader_parameter("plain_color",(original as StandardMaterial3D).albedo_color)
		entry.originals=[material];entry.override=material
		context_materials.append(material)
		_restore_entry(entry)

func _restore_entry(entry: Dictionary) -> void:
	entry.mesh.material_override=entry.override
	for i in entry.originals.size():entry.mesh.set_surface_override_material(i,entry.originals[i])
	entry.alpha=1.0;entry.active=false

func _build_reveal_sections() -> void:
	for i in 8:
		var r: Array=floor_layout.walk_rects[i]
		for door: Dictionary in floor_layout.doors:
			if door.kind!="room" or door.orientation!="H" or not door.locked:continue
			if absf(float(door.godot[2])-front_planes[i])>.14 or door.x<r[0] or door.x>r[2]:continue
			var room: Dictionary={}
			for candidate: Dictionary in floor_layout.rooms:
				if candidate.id==door.tag:room=candidate;break
			assert(not room.is_empty())
			var section := {"id":door.id,"corridor":i,"door":door,"span":Vector2(room.x1,room.x2),"plane":front_planes[i],"alpha":0.0,"latched":false,"release_time":0.0,"meshes":[],"materials":[],"state_window":null,"window_material":null,"applied_alpha":-1.0,"applied_visible":false}
			for entry in occluders:
				var source := entry.mesh as MeshInstance3D
				var record: Dictionary=floor_layout.receivers.get(str(source.name),{})
				if record.get("kind","") not in ["wall","door"]:continue
				if source.get_meta("occlusion_plane_axis",-1)!=2 or absf(float(source.get_meta("occlusion_plane",9999.0))-front_planes[i])>.14:continue
				var bounds := source.global_transform*source.get_aabb()
				if bounds.end.x<=room.x1 or bounds.position.x>=room.x2:continue
				var material := ShaderMaterial.new();material.shader=SECTION_V6
				for key in ["color_map","emission_map","irradiance_map","is_wall","lamp_power","baked_energy"]:material.set_shader_parameter(key,entry.originals[0].get_shader_parameter(key))
				material.set_shader_parameter("section_span",section.span)
				var copy := MeshInstance3D.new();copy.name="Reveal_"+door.id+"_"+str(source.name);copy.mesh=source.mesh
				copy.material_override=material;copy.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				add_child(copy);copy.global_transform=source.global_transform;copy.hide()
				section.meshes.append(copy);section.materials.append(material);baked_materials.append(material)
				if record.kind=="door":
					var window := MeshInstance3D.new();window.name="RevealStatus_"+door.id
					var quad := QuadMesh.new();quad.size=Vector2(.115,.045);window.mesh=quad
					var display_material := _unshaded_color(Color(.025,.045,.05,0.0))
					display_material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;window.material_override=display_material
					window.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
					add_child(window);window.position=Vector3(door.x,1.518,bounds.get_center().z-.004);window.hide()
					section.state_window=window;section.window_material=display_material
			assert(not section.meshes.is_empty() and section.state_window!=null,"Incomplete facade "+door.id)
			reveal_sections[door.id]=section

func _corridor_for(point: Vector3) -> int:
	if absf(point.y)>.3:return -1
	for i in 8:
		var r: Array=floor_layout.get("walk_rects",[])[i]
		if point.x>=r[0]-.05 and point.x<=r[2]+.05 and 4.2-point.z>=r[1]-.12 and 4.2-point.z<=r[3]+.12:return i
	return -1

func update_follow_camera() -> void:
	comparison_updating_camera=true
	super.update_follow_camera()
	comparison_updating_camera=false
	if not comparison_ready:return
	active_corridor=_corridor_for(player.position) if corridor_view and not overview_on else -1
	var camera := $ReviewCamera as Camera3D
	if active_corridor>=0:
		var config: Dictionary=CAMERA_CASES[camera_case]
		camera.position=player.position+Vector3(0,2.2,-float(config.distance))
		# The camera centre AND its near-plane margin remain outside the front wall.
		camera.position.z=minf(camera.position.z,front_planes[active_corridor]-.45)
		camera.look_at(player.position+Vector3(0,focus_height_m,0),Vector3.UP)
		camera.keep_aspect=Camera3D.KEEP_WIDTH;camera.fov=config.fov
	elif not overview_on:camera.fov=room_camera_fov
	_apply_comparison_visibility()

func _update_occlusion() -> void:
	if comparison_updating_camera:return
	if not comparison_ready:super._update_occlusion();return
	_apply_comparison_visibility()

func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	if not comparison_ready:return
	comparison_time+=delta
	_update_reveal_states(delta)
	_apply_comparison_visibility()

func _update_reveal_states(delta: float) -> void:
	var target := _interaction_door_target()
	for id: String in reveal_sections:
		var section: Dictionary=reveal_sections[id]
		var eligible: bool=active_corridor==section.corridor
		var normal: float=player.position.z-section.plane
		var lateral: float=absf(player.position.x-float(section.door.x))
		var entering: bool=eligible and normal>=0.0 and normal<=ENTER_DISTANCE and player.position.x>=section.span.x and player.position.x<=section.span.y
		var remaining: bool=eligible and normal>=0.0 and normal<=EXIT_DISTANCE and player.position.x>=section.span.x-.4 and player.position.x<=section.span.y+.4
		if trigger_case==1:entering=entering and lateral<=REGION_ENTER_HALF_WIDTH;remaining=remaining and lateral<=REGION_EXIT_HALF_WIDTH
		# An E request within the original interaction range keeps its real display readable.
		if eligible and target.get("id","")==id and locked_door_feedback[id].state!="idle":entering=true;remaining=true
		if wall_override==1:entering=false;remaining=false
		elif wall_override==2:
			entering=eligible and player.position.x>=section.span.x and player.position.x<=section.span.y;remaining=entering
		if not section.latched and entering:
			section.latched=true;section.release_time=0.0
			reveal_events.append({"time":comparison_time,"id":id,"visible":true,"rule":trigger_case})
		elif section.latched:
			if remaining:section.release_time=0.0
			else:
				section.release_time+=delta
				if section.release_time>=RELEASE_HOLD_SECONDS or not eligible or wall_override==1:
					section.latched=false;section.release_time=0.0
					reveal_events.append({"time":comparison_time,"id":id,"visible":false,"rule":trigger_case})
		var desired: float=REVEAL_LEVELS[reveal_level_index] if section.latched else 0.0
		section.alpha=move_toward(float(section.alpha),desired,delta*float(REVEAL_LEVELS[reveal_level_index])/FADE_SECONDS)

func _apply_comparison_visibility() -> void:
	var cutting := active_corridor>=0 and not overview_on
	var edge: float=front_planes[active_corridor]+.14 if cutting else 0.0
	if applied_corridor!=active_corridor:
		applied_corridor=active_corridor
		for material in context_materials:
			material.set_shader_parameter("clip_foreground",cutting);material.set_shader_parameter("foreground_edge_z",edge)
		for feedback: Dictionary in locked_door_feedback.values():
			for window: MeshInstance3D in feedback.windows:window.visible=not cutting or window.position.z>=edge
	if cutting:
		for entry in occluders:
			if entry.active:_restore_entry(entry)
	else:super._update_occlusion()
	for section: Dictionary in reveal_sections.values():
		var visible_now: bool=cutting and section.corridor==active_corridor and section.alpha>.001
		if visible_now!=section.applied_visible or not is_equal_approx(section.alpha,section.applied_alpha):
			for mesh: MeshInstance3D in section.meshes:mesh.visible=visible_now
			for material: ShaderMaterial in section.materials:material.set_shader_parameter("opacity",section.alpha)
			section.applied_visible=visible_now;section.applied_alpha=section.alpha
		section.state_window.visible=visible_now
		var color: Color=locked_door_feedback[section.id].material.albedo_color;color.a=section.alpha
		section.window_material.albedo_color=color

func _process(delta: float) -> void:
	super._process(delta)
	if comparison_ready:_apply_comparison_visibility()

func set_camera_case(index: int) -> void:
	camera_case=clampi(index,0,CAMERA_CASES.size()-1);update_follow_camera();_sync_render_camera();_sync_bloom_camera();_update_info()

func set_trigger_case(index: int) -> void:
	trigger_case=clampi(index,0,1)
	for section: Dictionary in reveal_sections.values():section.latched=false;section.release_time=0.0
	_update_info()

func camera_report() -> Dictionary:
	var camera := $ReviewCamera as Camera3D
	var head := camera.unproject_position(player.position+Vector3(0,1.65,0))
	var feet := camera.unproject_position(player.position)
	var result := {"case":CAMERA_CASES[camera_case].id,"position":str(camera.position),"fov":camera.fov,"keep_aspect":camera.keep_aspect,"corridor":active_corridor,"hero_head_y":head.y,"hero_feet_y":feet.y,"hero_height_px":feet.y-head.y,"camera_wall_gap":-1.0,"foreground_empty_fraction":-1.0}
	if active_corridor>=0:
		result.camera_wall_gap=front_planes[active_corridor]-.1-camera.position.z
		var floor_edge := camera.unproject_position(Vector3(player.position.x,.003,front_planes[active_corridor]+.103))
		result.foreground_empty_fraction=clampf((720.0-floor_edge.y)/720.0,0.0,1.0)
	return result

func _update_info() -> void:
	if not info:return
	var config: Dictionary=CAMERA_CASES[camera_case]
	var location := "正在比较走廊" if active_corridor>=0 else "室内/连接区沿用原镜头，F8进入走廊比较"
	info.text="4F 对比v6 · 1–5镜头 / T触发规则 / R显现强度 / F7自动、强制隐、强制显\n%s %s · 距离%.1fm · 水平FOV %.1f° · 高度2.2m · %s · 显现%d%% · %s\n%s · F8门外 · Home室内 · F11总览 · F12切区 · E认证/穿越\n当前为测试组合，未选定最终方案；100%%实体档只作遮挡对照"%[config.id,config.name,config.distance,config.fov,"沿墙距离" if trigger_case==0 else "门前区域",int(REVEAL_LEVELS[reveal_level_index]*100),["自动","强制隐","强制显"][wall_override],location]

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and comparison_ready:
		if review_ui.is_modal_open():return
		if event.physical_keycode>=KEY_1 and event.physical_keycode<=KEY_5:
			set_camera_case(event.physical_keycode-KEY_1);get_viewport().set_input_as_handled();return
		if event.physical_keycode==KEY_T:set_trigger_case(1-trigger_case);get_viewport().set_input_as_handled();return
		if event.physical_keycode==KEY_R:reveal_level_index=1-reveal_level_index;_update_info();get_viewport().set_input_as_handled();return
		if event.physical_keycode==KEY_F7:wall_override=(wall_override+1)%3;_update_info();get_viewport().set_input_as_handled();return
		if event.physical_keycode==KEY_HOME:
			overview_on=false;corridor_view=false;teleport_player(Vector3(10.5,.05,-8.2));update_follow_camera();get_viewport().set_input_as_handled();return
	super._unhandled_key_input(event)
