extends "res://scripts/dev/room1_surface_lighting_r7.gd"

const CONTACT_FLOOR_AGED := preload("res://assets/art/room1_floor_contact_r8/floor_aged.png")
const CONTACT_FLOOR_LEAKS := preload("res://assets/art/room1_floor_contact_r8/floor_with_leaks.png")
const CONTACT_IRRADIANCE := preload("res://assets/art/room1_floor_contact_r8/strip_irradiance_denoised.exr")
var floor_contact_enabled := true

func _ready() -> void:
	super._ready()
	if not Engine.is_editor_hint():
		set_floor_contact(true)
		set_surface_lighting(true)

func set_floor_contact(enabled: bool) -> void:
	floor_contact_enabled = enabled
	for material: ShaderMaterial in full_materials.get("Floor_continuous_no_tile_seams", []):
		material.set_shader_parameter("full_floor_aged_map", CONTACT_FLOOR_AGED if enabled else FLOOR_AGED)
		material.set_shader_parameter("full_floor_leaks_map", CONTACT_FLOOR_LEAKS if enabled else FLOOR_LEAKS)
	_update_info()

func set_surface_lighting(enabled: bool) -> void:
	var diagnostic := base_color_mode
	if diagnostic: set_base_color_mode(false)
	surface_lighting_enabled = enabled
	var texture := CONTACT_IRRADIANCE if enabled else SURFACE_IRRADIANCE
	for material: ShaderMaterial in baked_receivers:
		material.set_shader_parameter("strip_irradiance", texture)
	irradiance_path = texture.resource_path
	if diagnostic: set_base_color_mode(true)
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F:
		set_floor_contact(not floor_contact_enabled)
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 地坪接触旧化 r8 · %s · %s%s\nF 原地面/接触沉积 · I r7/r8配套光照 · N颜色图 · J回位 · WASD移动\n墙脚四边与20舱实际落地轮廓；布局、墙图、舱体、原灯带保持。" % ["新地面" if floor_contact_enabled else "r7原地面", "r8光照" if surface_lighting_enabled else "r7光照", " · Base Color" if base_color_mode else ""]
