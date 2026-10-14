@tool
extends "res://scripts/dev/room1_lighting_test.gd"

@export var screen_core_energy := 2.0
@export var window_light_energy := 0.16
@export var halo_intensity := 0.4
@export var halo_threshold := 0.5
var sample_view := 1
var halo_on := true
var local_light_on := true
var sample_ready := false

func _ready() -> void:
	window_lit_pods = PackedStringArray(["P12"])
	screen_lit_pods = PackedStringArray(["P12"])
	indirect_floor_energy = 0.22
	super._ready()
	$FollowTarget/ScaleMarker.visible = false
	var environment := $WorldEnvironment.environment as Environment
	environment.glow_enabled = true
	environment.glow_intensity = halo_intensity
	environment.glow_hdr_threshold = halo_threshold
	environment.glow_hdr_scale = 1.0
	environment.glow_bloom = 0.0
	# A bright source and a dim local light are separate controls.
	screen_materials["P12"].emission = Color(0.75, 0.95, 1.0)
	screen_materials["P12"].emission_energy_multiplier = screen_core_energy
	# Reduce printed reflections so the translucent pane does not resemble a lamp.
	glass_materials["P12"].albedo_texture = null
	glass_materials["P12"].albedo_color = Color(0.2, 0.35, 0.4, 0.2)
	glass_materials["P12"].transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	glass_materials["P12"].roughness = 0.3
	glass_materials["P12"].metallic_specular = 0.12
	# Local spill lights illuminate the casing, not their own emitting surface.
	$Pods/P12.find_child("pod_v3_glass", true, false).layers = 2
	window_backers["P12"].layers = 2
	$Pods/P12.find_child("pod_v3_display", true, false).layers = 4
	window_proxies["P12"].light_cull_mask = 1
	screen_proxies["P12"].light_cull_mask = 1
	window_proxies["P12"].global_position.y = $Pods/P12.global_position.y + 0.45
	window_proxies["P12"].light_energy = window_light_energy
	window_proxies["P12"].omni_range = 1.15
	screen_proxies["P12"].light_energy = 0.012
	screen_proxies["P12"].omni_range = 0.5
	sample_ready = true
	_set_sample_view(1)
	apply_sample_state()

func _process(_delta: float) -> void:
	# Closeup cameras stay fixed. This scene is not a character/camera-motion test.
	pass

func apply_sample_state() -> void:
	apply_lighting()
	glass_materials["P12"].emission_enabled = false
	window_backers["P12"].visible = false
	$WorldEnvironment.environment.glow_enabled = halo_on
	window_proxies["P12"].visible = local_light_on and windows_on
	screen_proxies["P12"].visible = local_light_on and screens_on
	_update_info()

func _set_sample_view(index: int) -> void:
	sample_view = index
	var pod := $Pods/P12 as Node3D
	var camera := $ReviewCamera as Camera3D
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.keep_aspect = Camera3D.KEEP_WIDTH
	match index:
		1:
			var mesh := pod.find_child("pod_v3_display", true, false) as MeshInstance3D
			var point := mesh.global_transform * mesh.mesh.get_aabb().get_center()
			camera.position = point + Vector3(0.3, 0.5, 1.6)
			camera.size = 1.6
			camera.look_at(point)
		2:
			var mesh := pod.find_child("pod_v3_glass", true, false) as MeshInstance3D
			var point := mesh.global_transform * mesh.mesh.get_aabb().get_center()
			camera.position = point + Vector3(0.7, 0.8, 1.1)
			camera.size = 1.55
			camera.look_at(point)
		3:
			camera.position = pod.global_position + Vector3(2.7, 2.4, 3.5)
			camera.size = 3.4
			camera.look_at(pod.global_position + Vector3(0, 0.5, 0))
		4:
			camera.projection = Camera3D.PROJECTION_PERSPECTIVE
			camera.fov = 50.0
			camera.position = Vector3(4.2, 2.2, 3.25)
			camera.basis = locked_basis
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if Engine.is_editor_hint() or not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_1: _set_sample_view(1)
		KEY_2: _set_sample_view(2)
		KEY_3: _set_sample_view(3)
		KEY_4: _set_sample_view(4)
		KEY_N: halo_on = not halo_on
		KEY_P: local_light_on = not local_light_on
		KEY_G: windows_on = not windows_on
		KEY_B: screens_on = not screens_on
		KEY_L: strip_on = not strip_on
		KEY_H: info.get_parent().visible = not info.get_parent().visible
	apply_sample_state()

func _update_info() -> void:
	if info:
		info.text = "荧光近景小样 / P12 · 待审\n1屏幕 2舱窗 3整舱 4室内\nN光晕 %s · P附近投光 %s · B屏幕 · G窗光 · L灯带 · H说明\n发光面、光晕与附近受光分开控制；仅此舱点亮。" % [halo_on, local_light_on]
