extends "res://scripts/dev/room1_floor_palette_r9.gd"

const STANDARD := preload("res://scenes/props/cryopod_standard_v8.tscn")
const STANDARD_ROOT := "res://assets/art/cryopod_standard_v8/"
var standard: Node3D
var standard_ready := false
var standard_bloom_meshes: Array[Dictionary] = []
var standard_bloom_screen: MeshInstance3D
var original_p12_collision_count := 0

func _ready() -> void:
	super._ready()
	$Pods/P12.visible = false
	for body in get_children():
		if body is StaticBody3D and str(body.name).begins_with("OpenP12_"):
			body.collision_layer = 0
			body.queue_free()
			original_p12_collision_count += 1
	standard = STANDARD.instantiate()
	$Pods.add_child(standard)
	standard.name = "P12_StandardV8"
	standard.global_transform = $Pods/P12.global_transform
	standard.set_pose_lightmaps(load(STANDARD_ROOT+"closed_irradiance.exr"),load(STANDARD_ROOT+"open_irradiance.exr"),continuous_baked_energy)
	standard.set_open_immediate(true)
	_build_standard_bloom()
	standard_ready = true
	apply_sample_state()
	call_deferred("position_structure_review")

func _build_standard_bloom() -> void:
	var world: Node3D = bloom_camera.get_parent()
	for mesh in world.get_children():
		if not mesh is MeshInstance3D or mesh.is_queued_for_deletion() or mesh == bloom_actor: continue
		if mesh.material_override == room_bloom_materials["P12"]:
			standard_bloom_screen = mesh
			var material:ShaderMaterial=room_bloom_materials["P12"]
			material.shader=preload("res://scripts/props/cryopod_standard_v8_1_screen.gdshader")
			material.set_shader_parameter("core_energy",1.0)
			material.set_shader_parameter("panel_backlight",0.0)
		elif mesh.global_position.distance_to($Pods/P12.global_position)<1.5:
			mesh.visible = false
			mesh.queue_free()
	var black := StandardMaterial3D.new()
	black.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	black.albedo_color = Color.BLACK
	black.cull_mode = BaseMaterial3D.CULL_DISABLED
	for source: MeshInstance3D in standard.get_model_root().find_children("*","MeshInstance3D",true,false):
		if str(source.name).contains("Glass") or source == standard.get_display_mesh(): continue
		var clone := MeshInstance3D.new()
		clone.mesh = source.mesh
		clone.material_override = black
		world.add_child(clone)
		standard_bloom_meshes.append({"source":source,"clone":clone})
	_sync_standard_visuals()

func _sync_standard_visuals() -> void:
	if not is_instance_valid(standard): return
	screen_proxies["P12"].visible = local_light_on and standard.screen_powered
	for item in standard_bloom_meshes:
		item.clone.global_transform = item.source.global_transform
		item.clone.visible = item.source.is_visible_in_tree()
	var display: MeshInstance3D = standard.get_display_mesh()
	if standard_bloom_screen and display:
		standard_bloom_screen.mesh = display.mesh
		standard_bloom_screen.global_transform = display.global_transform
		room_bloom_materials["P12"].set_shader_parameter("screen_pixels",standard.get_screen_texture())
		room_bloom_materials["P12"].set_shader_parameter("screen_overlay",standard.get_screen_overlay_texture())
		room_bloom_materials["P12"].set_shader_parameter("progress",standard.screen_progress)
		room_bloom_materials["P12"].set_shader_parameter("secondary_progress",standard.screen_secondary_progress)
		room_bloom_materials["P12"].set_shader_parameter("tertiary_progress",standard.screen_tertiary_progress)
		room_bloom_materials["P12"].set_shader_parameter("powered",1.0 if standard.screen_powered else 0.0)

func apply_sample_state() -> void:
	super.apply_sample_state()
	if not standard_ready: return
	window_proxies["P12"].light_energy = 0
	window_proxies["P12"].visible = false
	screen_proxies["P12"].visible = local_light_on and standard.screen_powered
	standard.set_baked_energy(continuous_baked_energy if strip_on else 0.0)
	_sync_standard_visuals()
	_update_info()

func _sync_actor_shadow() -> void:
	super._sync_actor_shadow()
	if standard_ready and actor_mesh:
		standard.set_actor_shadow_parameters(player.global_position,actor_mesh.global_transform*Vector3(0,-.605,0),actor_mesh.global_transform*Vector3(0,.605,0),actor_shadow_on)

func _process(delta: float) -> void:
	super._process(delta)
	if standard_ready: _sync_standard_visuals()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_O: standard.toggle()
			KEY_G: standard.set_tube_powered(not standard.tube_powered)
			KEY_B: standard.set_screen_powered(not standard.screen_powered)
			KEY_R:
				standard.set_open_immediate(false)
				standard.request_open()
			_: super._unhandled_key_input(event); return
		apply_sample_state()
		get_viewport().set_input_as_handled()

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 标准休眠舱 v8\nO开/关盖 · R重播开盖 · G内侧灯管 · B屏幕 · L墙灯 · J回位 · WASD\n单个真实动画模型，固定壳与随动盖碰撞；屏幕和灯管独立控制。"
