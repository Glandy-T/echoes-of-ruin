@tool
extends "res://scripts/dev/room1_glow_sample.gd"

var reflection_on := true
var pixel_glass: ShaderMaterial
var soft_screen: ShaderMaterial

func _ready() -> void:
	super._ready()
	var glass := $Pods/P12.find_child("pod_v3_glass", true, false) as MeshInstance3D
	var original := glass.mesh.surface_get_material(0) as BaseMaterial3D
	pixel_glass = ShaderMaterial.new()
	pixel_glass.shader = preload("res://scripts/dev/room1_pixel_transparent_glass.gdshader")
	pixel_glass.set_shader_parameter("pixel_reflections", original.albedo_texture)
	glass.set_surface_override_material(0, pixel_glass)
	var display := $Pods/P12.find_child("pod_v3_display", true, false) as MeshInstance3D
	soft_screen = ShaderMaterial.new()
	soft_screen.shader = preload("res://scripts/dev/room1_screen_soft_emission.gdshader")
	soft_screen.set_shader_parameter("screen_pixels", screen_materials["P12"].albedo_texture)
	soft_screen.set_shader_parameter("core_energy", screen_core_energy)
	display.set_surface_override_material(0, soft_screen)
	apply_sample_state()

func apply_sample_state() -> void:
	super.apply_sample_state()
	if pixel_glass:
		pixel_glass.set_shader_parameter("reflection_strength", 1.0 if reflection_on else 0.0)
	if soft_screen:
		soft_screen.set_shader_parameter("powered", 1.0 if screens_on else 0.0)
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	super._unhandled_key_input(event)
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_V:
		reflection_on = not reflection_on
		apply_sample_state()

func _update_info() -> void:
	if info:
		info.text = "荧光小样 r2 / 像素反射＋透明玻璃 · 待审\n1屏幕 2舱窗 3整舱 4室内\nV像素反射 %s · N光晕 %s · P附近投光 · B屏幕 · G窗光 · H说明\n屏幕文字/状态条主发光，边框减弱。仅此舱点亮。" % [reflection_on, halo_on]
