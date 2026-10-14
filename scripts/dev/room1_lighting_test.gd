@tool
extends "res://scripts/dev/room1_camera_bounds_test.gd"

@export var window_lit_pods := PackedStringArray(["P02", "P12", "P17"])
@export var screen_lit_pods := PackedStringArray(["P02", "P12", "P17"])
@export_range(0.0, 1.0) var strip_surface_energy := 0.38
@export_range(0.0, 1.0) var strip_light_energy := 0.24
@export_range(0.0, 1.0) var indirect_floor_energy := 0.12
var strip_on := true
var windows_on := true
var screens_on := true
var strip_materials: Array[ShaderMaterial] = []
var window_materials: Dictionary = {}
var glass_materials: Dictionary = {}
var window_backers: Dictionary = {}
var screen_materials: Dictionary = {}
var window_proxies: Dictionary = {}
var screen_proxies: Dictionary = {}
var lighting_ready := false

func _ready() -> void:
	super._ready()
	$ReviewLights.visible = false
	$WorldEnvironment.environment = $WorldEnvironment.environment.duplicate()
	$WorldEnvironment.environment.ambient_light_energy = indirect_floor_energy
	var white := _solid_texture(Color.WHITE)
	var black := _solid_texture(Color.BLACK)
	for mesh: MeshInstance3D in $Shell.find_children("*", "MeshInstance3D", true, false):
		mesh.material_override = null
		for surface in mesh.mesh.get_surface_count():
			var source := mesh.mesh.surface_get_material(surface) as BaseMaterial3D
			if source == null or not source.resource_name.contains("MATERIAL_REVISION"):
				continue
			var material := ShaderMaterial.new()
			material.shader = preload("res://scripts/dev/room1_continuous_strip.gdshader")
			material.set_shader_parameter("color_map", source.albedo_texture if source.albedo_texture else white)
			material.set_shader_parameter("base_color", source.albedo_color)
			material.set_shader_parameter("emission_map", source.emission_texture if source.emission_texture else black)
			material.set_shader_parameter("has_emission_map", 1.0 if source.emission_texture else 0.0)
			if mesh.name == "Wall_left":
				material.set_shader_parameter("uv_offset", Vector3(4.75 / 9.1, -0.5, 0))
			mesh.set_surface_override_material(surface, material)
			strip_materials.append(material)
	var proxies := Node3D.new()
	proxies.name = "PodLightProxies"
	add_child(proxies)
	var body_material_cache := {}
	for pod: Node3D in $Pods.get_children():
		var glass := pod.find_child("pod_v3_glass", true, false) as MeshInstance3D
		var display := pod.find_child("pod_v3_display", true, false) as MeshInstance3D
		for mesh: MeshInstance3D in pod.find_children("*", "MeshInstance3D", true, false):
			if mesh == glass or mesh == display:
				continue
			mesh.material_override = null
			for surface in mesh.mesh.get_surface_count():
				var source := mesh.mesh.surface_get_material(surface) as BaseMaterial3D
				if not body_material_cache.has(source.get_instance_id()):
					var body := ShaderMaterial.new()
					body.shader = preload("res://scripts/dev/room1_continuous_strip.gdshader")
					body.set_shader_parameter("color_map", source.albedo_texture if source.albedo_texture else white)
					body.set_shader_parameter("base_color", source.albedo_color)
					body.set_shader_parameter("emission_map", black)
					body_material_cache[source.get_instance_id()] = body
					strip_materials.append(body)
				mesh.set_surface_override_material(surface, body_material_cache[source.get_instance_id()])
		var window := (glass.mesh.surface_get_material(0) as BaseMaterial3D).duplicate() as BaseMaterial3D
		window.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
		window.albedo_color = Color(0.65, 0.85, 0.9, 0.35)
		window.roughness = 0.22
		window.metallic_specular = 0.4
		window.emission_enabled = false
		glass.material_override = null
		glass.set_surface_override_material(0, window)
		glass_materials[pod.name] = window
		var backer := MeshInstance3D.new()
		backer.name = "WindowInteriorGlowCandidate"
		backer.mesh = glass.mesh
		backer.position.y = -0.025
		glass.add_child(backer)
		var inside := StandardMaterial3D.new()
		inside.albedo_color = Color(0.08, 0.2, 0.24)
		inside.emission = Color(0.2, 0.5, 0.58)
		inside.emission_energy_multiplier = 0.45
		inside.roughness = 1.0
		inside.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		backer.material_override = inside
		window_materials[pod.name] = inside
		window_backers[pod.name] = backer
		var screen := (display.mesh.surface_get_material(0) as BaseMaterial3D).duplicate() as BaseMaterial3D
		screen.emission_texture = screen.albedo_texture
		screen.emission_operator = BaseMaterial3D.EMISSION_OP_MULTIPLY
		screen.emission = Color(0.55, 0.9, 0.95)
		screen.emission_energy_multiplier = 0.45
		screen.metallic_specular = 0.0
		display.material_override = null
		display.set_surface_override_material(0, screen)
		screen_materials[pod.name] = screen
		var window_position := glass.global_transform * glass.mesh.get_aabb().get_center() + Vector3(0, 0.1, 0)
		window_proxies[pod.name] = _pod_light(proxies, "Window_" + pod.name, window_position, 1.6, 0.08)
		var screen_position := display.global_transform * display.mesh.get_aabb().get_center() + pod.basis * Vector3(0, 0.03, 0.12)
		screen_proxies[pod.name] = _pod_light(proxies, "Screen_" + pod.name, screen_position, 0.75, 0.08)
	lighting_ready = true
	apply_lighting()
	_update_info()

func apply_lighting() -> void:
	for material in strip_materials:
		material.set_shader_parameter("strip_surface_energy", strip_surface_energy if strip_on else 0.0)
		material.set_shader_parameter("strip_light_energy", strip_light_energy if strip_on else 0.0)
	for id in window_materials:
		var powered := windows_on and window_lit_pods.has(id)
		window_materials[id].emission_enabled = powered
		window_backers[id].visible = powered
		window_proxies[id].visible = powered
	for id in screen_materials:
		var powered := screens_on and screen_lit_pods.has(id)
		screen_materials[id].emission_enabled = powered
		screen_materials[id].albedo_color = Color.WHITE if powered else Color(0.12, 0.12, 0.12)
		screen_proxies[id].visible = powered

func _pod_light(parent: Node3D, node_name: String, point: Vector3, radius: float, energy: float) -> OmniLight3D:
	var light := OmniLight3D.new()
	light.name = node_name
	parent.add_child(light)
	light.global_position = point
	light.light_color = Color("96c7d0")
	light.light_energy = energy
	light.light_specular = 0.0
	light.omni_range = radius
	light.omni_attenuation = 2.5
	light.shadow_enabled = true
	return light

func _solid_texture(color: Color) -> ImageTexture:
	var image := Image.create(1, 1, false, Image.FORMAT_RGB8)
	image.fill(color)
	return ImageTexture.create_from_image(image)

func _unhandled_key_input(event: InputEvent) -> void:
	super._unhandled_key_input(event)
	if Engine.is_editor_hint() or not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_L: strip_on = not strip_on
		KEY_G: windows_on = not windows_on
		KEY_B: screens_on = not screens_on
	apply_lighting()
	_update_info()

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 室内照明试排 · 3舱亮、17舱停机\nWASD移动 · 1–9位置 · R复位 · T标记 · H说明\nL灯带 %s · G窗光 %s · B屏幕 %s\n亮舱 P02/P12/P17为临时试排；窗面透光候选待审。" % [strip_on, windows_on, screens_on]
