@tool
extends "res://scripts/dev/room1_glow_sample_r4.gd"

@export_range(0.0, 0.25) var room_ambient_energy := 0.025
@export_range(0.0, 2.0) var actual_strip_energy := 0.35
var actual_strip_lights: Array[Light3D] = []
var room_screen_shaders: Dictionary = {}
var room_glass_shaders: Dictionary = {}
var room_bloom_materials: Dictionary = {}
var room_ready := false
var shadows_on := true
var movement_view := true
var floor_chunk_count := 0

func _ready() -> void:
	super._ready()
	window_lit_pods = PackedStringArray(["P02", "P12", "P17"])
	screen_lit_pods = PackedStringArray(["P02", "P12", "P17"])
	strip_surface_energy = 0.7
	strip_light_energy = 0.0
	$WorldEnvironment.environment.ambient_light_energy = room_ambient_energy
	$WorldEnvironment.environment.ambient_light_sky_contribution = 0.0
	for pod: Node3D in $Pods.get_children():
		var id := str(pod.name)
		var glass := pod.find_child("pod_v3_glass", true, false) as MeshInstance3D
		var display := pod.find_child("pod_v3_display", true, false) as MeshInstance3D
		var source := glass.mesh.surface_get_material(0) as BaseMaterial3D
		var pane := ShaderMaterial.new()
		pane.shader = preload("res://scripts/dev/room1_glass_room_r2.gdshader")
		pane.set_shader_parameter("pixel_reflections", source.albedo_texture)
		glass.set_surface_override_material(0, pane)
		glass.layers = 2
		glass.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		room_glass_shaders[id] = pane
		window_backers[id].visible = false
		var screen := ShaderMaterial.new()
		screen.shader = preload("res://scripts/dev/room1_screen_diffuse_core_r4.gdshader")
		screen.set_shader_parameter("screen_pixels", screen_materials[id].albedo_texture)
		screen.set_shader_parameter("core_energy", screen_core_energy)
		display.set_surface_override_material(0, screen)
		display.layers = 4
		room_screen_shaders[id] = screen
		window_proxies[id].global_position.y = pod.global_position.y + 0.45
		window_proxies[id].light_energy = window_light_energy
		window_proxies[id].omni_range = 1.15
		window_proxies[id].light_cull_mask = 1
		screen_proxies[id].light_energy = 0.004
		screen_proxies[id].omni_range = 0.65
		screen_proxies[id].omni_attenuation = 1.5
		screen_proxies[id].light_cull_mask = 1
	_build_strip_lights()
	if bloom_camera:
		room_bloom_materials["P12"] = bloom_material
		_add_room_bloom_emitter("P02")
		_add_room_bloom_emitter("P17")
	floor_chunk_count = preload("res://scripts/dev/room1_floor_light_chunks_r2.gd").partition($Shell)
	$FollowTarget/ScaleMarker.visible = true
	$FollowTarget.position = START
	$ReviewCamera.projection = Camera3D.PROJECTION_PERSPECTIVE
	$ReviewCamera.keep_aspect = Camera3D.KEEP_WIDTH
	$ReviewCamera.fov = horizontal_fov_degrees
	room_ready = true
	update_follow_camera()
	apply_sample_state()

func _build_strip_lights() -> void:
	var group := Node3D.new()
	group.name = "ActualStripLights"
	add_child(group)
	# Eight spotlights and six omnis fit Compatibility's separate per-type limits.
	for index in 8:
		var light := SpotLight3D.new()
		group.add_child(light)
		light.position = Vector3(1.4 + index * 2.6, 2.96, -9.08)
		light.look_at(light.position + Vector3(0.0, -2.0, 1.1))
		light.spot_range = 7.0
		light.spot_angle = 82.0
		light.spot_attenuation = 0.7
		light.spot_angle_attenuation = 0.1
		_configure_strip_light(light, actual_strip_energy * 0.55)
	for x in [2.65, 7.55, 12.95, 18.35]:
		var light := OmniLight3D.new()
		group.add_child(light)
		light.position = Vector3(x, 2.96, -0.42)
		light.omni_range = 6.0
		light.omni_attenuation = 0.9
		_configure_strip_light(light, actual_strip_energy * 0.3)
	for x in [0.42, 20.58]:
		var light := OmniLight3D.new()
		group.add_child(light)
		light.position = Vector3(x, 2.96, -4.75)
		light.omni_range = 5.0
		light.omni_attenuation = 1.2
		_configure_strip_light(light, actual_strip_energy * 0.22)

func _configure_strip_light(light: Light3D, energy: float) -> void:
	light.light_color = Color("adcbd1")
	light.light_energy = energy
	light.light_specular = 0.05
	light.shadow_enabled = true
	light.shadow_bias = 0.12
	light.shadow_normal_bias = 1.5
	light.light_cull_mask = 1 | 2
	actual_strip_lights.append(light)

func _add_room_bloom_emitter(id: String) -> void:
	var display := get_node("Pods/" + id).find_child("pod_v3_display", true, false) as MeshInstance3D
	var world := bloom_camera.get_parent()
	for object in world.get_children():
		if object is MeshInstance3D and object.mesh == display.mesh and object.global_position.distance_to(display.global_position) < 0.001:
			object.queue_free()
	var emitter := MeshInstance3D.new()
	emitter.mesh = display.mesh
	var material := ShaderMaterial.new()
	material.shader = preload("res://scripts/dev/room1_screen_bloom_source_r4.gdshader")
	material.set_shader_parameter("screen_pixels", screen_materials[id].albedo_texture)
	emitter.material_override = material
	world.add_child(emitter)
	emitter.global_transform = display.global_transform
	room_bloom_materials[id] = material

func apply_sample_state() -> void:
	super.apply_sample_state()
	if not room_ready:
		return
	for material in strip_materials:
		material.set_shader_parameter("strip_light_energy", 0.0)
	for light in actual_strip_lights:
		light.visible = strip_on
		light.shadow_enabled = shadows_on
	for id in room_screen_shaders:
		var screen_powered: bool = screens_on and screen_lit_pods.has(id)
		var window_powered: bool = windows_on and window_lit_pods.has(id)
		room_screen_shaders[id].set_shader_parameter("powered", 1.0 if screen_powered else 0.0)
		room_glass_shaders[id].set_shader_parameter("reflection_strength", 1.0 if reflection_on else 0.0)
		window_backers[id].visible = false
		window_proxies[id].visible = local_light_on and window_powered
		screen_proxies[id].visible = local_light_on and screen_powered
	for id in room_bloom_materials:
		room_bloom_materials[id].set_shader_parameter("powered", 1.0 if screens_on and screen_lit_pods.has(id) else 0.0)
	$WorldEnvironment.environment.glow_enabled = false
	_update_info()

func _process(delta: float) -> void:
	if Engine.is_editor_hint() or not room_ready:
		return
	if movement_view:
		var movement := Vector2(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)), float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W)))
		move_marker(movement, delta)
	if bloom_camera:
		_sync_bloom_camera()

func _unhandled_key_input(event: InputEvent) -> void:
	if Engine.is_editor_hint() or not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.physical_keycode >= KEY_1 and event.physical_keycode <= KEY_9:
		movement_view = true
		$FollowTarget.position = EDGE_POSITIONS[event.physical_keycode - KEY_1]
		update_follow_camera()
	match event.physical_keycode:
		KEY_R:
			movement_view = true
			$FollowTarget.position = START
			update_follow_camera()
		KEY_L: strip_on = not strip_on
		KEY_G: windows_on = not windows_on
		KEY_B: screens_on = not screens_on
		KEY_N: halo_on = not halo_on
		KEY_P: local_light_on = not local_light_on
		KEY_K: shadows_on = not shadows_on
		KEY_T: $FollowTarget/ScaleMarker.visible = not $FollowTarget/ScaleMarker.visible
		KEY_H: info.get_parent().visible = not info.get_parent().visible
	apply_sample_state()

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 整体照明 r2 · 待审\nWASD移动 · 1–9中央/边缘 · R复位 · T标记 · H说明\nL灯带 %s · K阴影 %s · G舱内光 · B屏幕 · N光晕\n环境底光0.025；真实灯带投光，无旧均匀填光。3亮舱为临时分布。" % [strip_on, shadows_on]
