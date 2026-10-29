extends "res://scripts/dev/room1_integrated_door_pixellab_v7.gd"

const NEW_WALLS := [preload("res://assets/art/room1_wall_pixellab_r11/wall_left.png"), preload("res://assets/art/room1_wall_pixellab_r11/wall_right.png"), preload("res://assets/art/room1_wall_pixellab_r11/wall_front.png"), preload("res://assets/art/room1_wall_pixellab_r11/wall_rear.png")]
var wall_rework_on := true

func _ready() -> void:
	super._ready()
	if not Engine.is_editor_hint(): set_wall_rework(true)

func set_wall_rework(enabled: bool) -> void:
	wall_rework_on = enabled
	var maps := NEW_WALLS if enabled else [CONTACT_MAPS[0], CONTACT_MAPS[1], CONTACT_MAPS[2], PORTAL_WALL]
	for name in full_materials:
		if name == "Floor_continuous_no_tile_seams": continue
		for material: ShaderMaterial in full_materials[name]:
			for i in 4:
				material.set_shader_parameter(["full_wall_left_map", "full_wall_right_map", "full_wall_front_map", "full_wall_rear_map"][i], maps[i])
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_B, KEY_V, KEY_M]:
		set_wall_rework(not wall_rework_on); get_viewport().set_input_as_handled(); return
	super._unhandled_key_input(event)

func _update_info() -> void:
	super._update_info()
	if info: info.text += "\nB 四墙材质：" + ("PixelLab r11 全新旧化" if wall_rework_on else "旧r6对照")
