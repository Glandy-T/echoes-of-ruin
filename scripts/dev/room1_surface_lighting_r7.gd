extends "res://scripts/dev/room1_seam_contact_r6.gd"

const SURFACE_IRRADIANCE := preload("res://assets/art/room1_surface_lighting_r7/strip_irradiance_denoised.exr")
const ORIGINAL_IRRADIANCE := preload("res://assets/art/room1_wall_finish_r4/strip_irradiance_denoised.exr")
var surface_lighting_enabled := true

func _ready() -> void:
	super._ready()
	if not Engine.is_editor_hint(): set_surface_lighting(true)

func set_surface_lighting(enabled: bool) -> void:
	var diagnostic := base_color_mode
	if diagnostic: set_base_color_mode(false)
	surface_lighting_enabled = enabled
	var texture := SURFACE_IRRADIANCE if enabled else ORIGINAL_IRRADIANCE
	for material: ShaderMaterial in baked_receivers:
		material.set_shader_parameter("strip_irradiance", texture)
	irradiance_path = texture.resource_path
	if diagnostic: set_base_color_mode(true)
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_I:
		set_surface_lighting(not surface_lighting_enabled)
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	super._update_info()
	if info: info.text += "\nI 配套间接光：" + ("r7 当前墙地重烘" if surface_lighting_enabled else "r4 旧光照对照")
