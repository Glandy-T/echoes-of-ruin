extends "res://scripts/dev/room1_floor_contact_r8.gd"
const NEUTRAL_FLOOR_AGED := preload("res://assets/art/room1_floor_palette_r9/floor_aged.png")
const NEUTRAL_FLOOR_LEAKS := preload("res://assets/art/room1_floor_palette_r9/floor_with_leaks.png")
const NEUTRAL_IRRADIANCE := preload("res://assets/art/room1_floor_palette_r9/strip_irradiance_denoised.exr")

func set_floor_contact(enabled: bool) -> void:
	floor_contact_enabled = enabled
	for material: ShaderMaterial in full_materials.get("Floor_continuous_no_tile_seams", []):
		material.set_shader_parameter("full_floor_aged_map", NEUTRAL_FLOOR_AGED if enabled else CONTACT_FLOOR_AGED)
		material.set_shader_parameter("full_floor_leaks_map", NEUTRAL_FLOOR_LEAKS if enabled else CONTACT_FLOOR_LEAKS)
	_update_info()

func set_surface_lighting(enabled: bool) -> void:
	var diagnostic := base_color_mode
	if diagnostic: set_base_color_mode(false)
	surface_lighting_enabled = enabled
	var texture := NEUTRAL_IRRADIANCE if enabled else CONTACT_IRRADIANCE
	for material: ShaderMaterial in baked_receivers: material.set_shader_parameter("strip_irradiance", texture)
	irradiance_path = texture.resource_path
	if diagnostic: set_base_color_mode(true)
	_update_info()

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 地面冷灰蓝配色 r9 · %s\nF r8偏黄绿/r9冷灰蓝 · I配套光照对照 · N颜色图 · J回位 · WASD移动\n只调整沉积和干涸边配色，形状、位置、模型和灯带参数保持。" % ["r9冷灰蓝" if floor_contact_enabled else "r8旧配色"]
