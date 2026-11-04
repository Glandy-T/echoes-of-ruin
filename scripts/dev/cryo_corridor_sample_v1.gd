extends "res://scripts/dev/room1_door_window_r30.gd"

const SAMPLE := preload("res://assets/art/cryo_corridor_sample_v1/corridor_sample_v1.glb")
const SAMPLE_LAYER := 1 << 19
var corridor_sample: Node3D
var sample_lights: Node3D
var sample_on := true
var corridor_view := false
var switching_view := false
var fade_rect: ColorRect
var occluders: Array[Dictionary] = []
var camera_events: Array[Dictionary] = []
var input_release_required := false
var authentication_requested := false
var authentication_prompt_visible := false
var corridor_lamps_on := true
var corridor_lamp_materials: Array[StandardMaterial3D] = []

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint(): return
	# Stationary, opaque, double-sided portal curtain: never reveal the other area.
	var curtain := get_node("BlackDoorway") as MeshInstance3D
	curtain.mesh=curtain.mesh.duplicate()
	(curtain.mesh as QuadMesh).size=Vector2(1.44,2.44)
	curtain.visible=true
	corridor_sample=SAMPLE.instantiate()
	corridor_sample.name="CorridorSampleV1"
	add_child(corridor_sample)
	for item in corridor_sample.find_children("*","MeshInstance3D",true,false):
		var mesh := item as MeshInstance3D
		mesh.layers=1 | SAMPLE_LAYER
		for i in mesh.mesh.get_surface_count():
			var mat := mesh.mesh.surface_get_material(i).duplicate() as StandardMaterial3D
			mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_NEAREST
			mat.roughness=1.0
			mat.metallic_specular=0.0
			if "Wall" in str(mesh.name):
				mat.shading_mode=BaseMaterial3D.SHADING_MODE_PER_PIXEL
				mat.emission_enabled=true
				mat.emission=Color(.65,.85,.9)
				mat.emission_texture=load("res://assets/art/cryo_corridor_sample_v1/wall_emission.png")
				mat.emission_operator=BaseMaterial3D.EMISSION_OP_MULTIPLY
				mat.emission_energy_multiplier=0.35
				corridor_lamp_materials.append(mat)
			mesh.set_surface_override_material(i,mat)
	sample_lights=Node3D.new()
	sample_lights.name="CorridorSampleLights"
	add_child(sample_lights)
	for z in [-11.65,-9.75]:
		for x in [7.15,8.2,9.25]:
			var light := OmniLight3D.new()
			light.position=Vector3(x,3.04,z)
			light.omni_range=4.4
			light.light_energy=0.5
			light.light_color=Color(.80,.91,1.0)
			light.light_cull_mask=SAMPLE_LAYER
			light.shadow_enabled=false
			sample_lights.add_child(light)
	var canvas := CanvasLayer.new()
	canvas.layer=100
	add_child(canvas)
	fade_rect=ColorRect.new()
	fade_rect.color=Color(0,0,0,0)
	fade_rect.mouse_filter=Control.MOUSE_FILTER_IGNORE
	fade_rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	canvas.add_child(fade_rect)
	for root in [get_node("OutsideRoute"),corridor_sample]:
		for item in root.find_children("*","MeshInstance3D",true,false):
			var mesh := item as MeshInstance3D
			if mesh.get_aabb().size.y < .05:continue
			var originals: Array[Material] = []
			var faded: Array[StandardMaterial3D] = []
			for i in mesh.mesh.get_surface_count():
				var original := mesh.get_active_material(i)
				if not original is StandardMaterial3D:continue
				originals.append(original)
				var ghost := original.duplicate() as StandardMaterial3D
				ghost.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
				ghost.albedo_color.a=.12
				ghost.no_depth_test=false
				faded.append(ghost)
			if not originals.is_empty():occluders.append({"mesh":mesh,"originals":originals,"faded":faded,"active":false,"override":mesh.material_override})
	_update_info()

func set_sample_visible(enabled: bool) -> void:
	sample_on=enabled
	corridor_sample.visible=enabled
	sample_lights.visible=enabled and corridor_lamps_on
	_update_info()

func set_corridor_lamps(enabled: bool) -> void:
	corridor_lamps_on=enabled
	sample_lights.visible=sample_on and enabled
	for mat in corridor_lamp_materials:
		mat.emission_enabled=enabled
	for entry in occluders:
		if "Wall" in str(entry.mesh.name):
			for mat in entry.faded:
				mat.emission_enabled=enabled

func update_follow_camera() -> void:
	super.update_follow_camera()
	if not has_node("FollowTarget"):return
	var target := $FollowTarget as Node3D
	# User-requested provisional 180-degree reverse of the Room 1 camera.
	# Other-room walls between camera and actor become ghosts, collision retained.
	if corridor_view and target.position.z > -36.2:
		var camera := $ReviewCamera as Camera3D
		camera.position=target.position+Vector3(0,camera_height_m,-camera_distance_m)
		camera.look_at(target.position+Vector3(0,focus_height_m,0),Vector3.UP)
	_update_occlusion()

func _update_occlusion() -> void:
	if occluders.is_empty() or not player:return
	var camera := $ReviewCamera as Camera3D
	for entry in occluders:
		var mesh := entry.mesh as MeshInstance3D
		var blocked := false
		if not entry.has("world_box"):entry.world_box=mesh.global_transform*mesh.get_aabb()
		var bounds: AABB=entry.world_box
		var end := bounds.position+bounds.size
		var in_view_strip := end.x>=minf(camera.position.x,player.position.x)-4.1 and bounds.position.x<=maxf(camera.position.x,player.position.x)+4.1 and end.z>=minf(camera.position.z,player.position.z)-.15 and bounds.position.z<=maxf(camera.position.z,player.position.z)+.15 and end.y>=player.position.y and bounds.position.y<=camera.position.y+1.0
		if not in_view_strip and not entry.active:continue
		if not mesh.is_visible_in_tree() and not entry.active:continue
		if corridor_view and in_view_strip:
			var inverse := mesh.global_transform.affine_inverse()
			# Cover the visible aisle around the actor, not just a person-sized hole.
			# Otherwise the adjacent room's two long wall bays still cover the screen.
			for offset in _occlusion_offsets_for(mesh):
				if mesh.get_aabb().grow(.08).intersects_segment(inverse*camera.global_position,inverse*(player.global_position+offset)) != null:
					blocked=true
					break
		var alpha := float(entry.get("alpha",1.0))
		alpha=move_toward(alpha,_occlusion_opacity() if blocked else 1.0,get_physics_process_delta_time()*4.4)
		entry.alpha=alpha
		if alpha < .999:
			mesh.material_override=null
			for i in entry.faded.size():
				if entry.faded[i] is ShaderMaterial:entry.faded[i].set_shader_parameter("opacity",alpha)
				else:entry.faded[i].albedo_color.a=alpha
				mesh.set_surface_override_material(i,entry.faded[i])
		elif entry.active:
			mesh.material_override=entry.override
			for i in entry.originals.size():mesh.set_surface_override_material(i,entry.originals[i])
		entry.active=alpha < .999

func _occlusion_probe_offsets() -> Array[Vector3]:
	return [Vector3(-4,.15,0),Vector3(-2,.15,0),Vector3(0,.15,0),Vector3(2,.15,0),Vector3(4,.15,0),Vector3(-4,1.65,0),Vector3(-2,1.65,0),Vector3(0,1.65,0),Vector3(2,1.65,0),Vector3(4,1.65,0)]

func _occlusion_offsets_for(_mesh: MeshInstance3D) -> Array[Vector3]:
	return _occlusion_probe_offsets()

func _occlusion_opacity() -> float:
	return .12

func _physics_process(delta: float) -> void:
	var near_door := _near_authentication_door()
	if not near_door:authentication_requested=false
	# Gate the inherited sensor/scan state before its physics update.
	door_occupied=near_door and authentication_requested
	var saved_mode := test_mode
	var saved_input := test_input
	var raw_input := Vector2(float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT))-float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN))-float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
	if input_release_required and raw_input==Vector2.ZERO:input_release_required=false
	if switching_view or (input_release_required and not test_mode):
		test_mode=true
		test_input=Vector2.ZERO
	elif _reverse_corridor_controls() and not test_mode:
		test_mode=true
		test_input=-raw_input
	super._physics_process(delta)
	test_mode=saved_mode
	test_input=saved_input
	if fade_rect and player and not switching_view and _automatic_portal_crossing_enabled():
		if not corridor_view and player.position.z < -9.72: _switch_view(true)
		elif corridor_view and player.position.z > -9.25: _switch_view(false)

func _automatic_portal_crossing_enabled() -> bool:
	return true

func _reverse_corridor_controls() -> bool:
	return corridor_view and player and player.position.z > -36.2

func _near_authentication_door() -> bool:
	return is_instance_valid(player) and is_instance_valid(door_mesh) and absf(player.position.x-door_closed_position.x)<1.35 and absf(player.position.z-door_closed_position.z)<1.8

func _process(delta: float) -> void:
	super._process(delta)
	if not is_instance_valid(exit_anchor):return
	var show := _near_authentication_door() and not authentication_requested and not switching_view
	if show!=authentication_prompt_visible:
		authentication_prompt_visible=show
		if show:review_ui.show_interaction_name(door_sensor,"E：ドア認証",exit_anchor,Vector2(0,-35))
		else:review_ui.hide_interaction_name(door_sensor)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact") and not switching_view and _near_authentication_door() and review_ui.can_accept_world_interaction():
		authentication_requested=true
		get_viewport().set_input_as_handled()
		return
	super._unhandled_input(event)

func _switch_view(outside: bool) -> void:
	switching_view=true
	camera_events.append({"event":"fade_out","outside":outside})
	var tween := create_tween()
	tween.tween_property(fade_rect,"color:a",1.0,.22)
	await tween.finished
	corridor_view=outside
	update_follow_camera()
	_sync_render_camera()
	_sync_bloom_camera()
	camera_events.append({"event":"rotated_under_black","outside":outside,"alpha":fade_rect.color.a})
	await get_tree().create_timer(.08).timeout
	tween=create_tween()
	tween.tween_property(fade_rect,"color:a",0.0,.30)
	await tween.finished
	switching_view=false
	input_release_required=true
	camera_events.append({"event":"fade_in_complete","outside":outside})

func _update_info() -> void:
	super._update_info()
	if info:
		info.text="4F走廊小样 v1 / " + ("墙板候选 · 复用r26地坪" if sample_on else "原灰盒") + "\nE 门认证 · F7 灰盒/小样 · F8 小样位置 · F9灯带 · WASD移动。门洞双面黑色。"

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode==KEY_F9:
			set_corridor_lamps(not corridor_lamps_on)
			get_viewport().set_input_as_handled()
			return
		if event.physical_keycode==KEY_F7:
			set_sample_visible(not sample_on)
			get_viewport().set_input_as_handled()
			return
		if event.physical_keycode==KEY_F8:
			teleport_player(Vector3(8.2,.05,-10.7))
			get_viewport().set_input_as_handled()
			return
	super._unhandled_key_input(event)
