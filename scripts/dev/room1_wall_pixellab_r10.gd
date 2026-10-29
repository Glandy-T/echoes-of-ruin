extends "res://scripts/dev/room1_integrated_door_pixellab_v7.gd"

const WALL_REWORK := preload("res://assets/art/room1_wall_pixellab_r10/wall_left.png")
var wall_rework_on := true

func _ready() -> void:
	super._ready()
	if not Engine.is_editor_hint():
		set_wall_rework(true)

func set_wall_rework(enabled: bool) -> void:
	wall_rework_on = enabled
	for material: ShaderMaterial in full_materials.get("Wall_left", []):
		material.set_shader_parameter("full_wall_left_map", WALL_REWORK if enabled else CONTACT_MAPS[0])
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_B, KEY_V]:
		set_wall_rework(not wall_rework_on)
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	super._update_info()
	if info:
		info.text += "\nB 左墙 PixelLab 样段：" + ("r10" if wall_rework_on else "原r6")
