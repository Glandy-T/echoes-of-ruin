extends "res://scripts/dev/room1_surface_full_r5.gd"

const CONTACT_MAPS := [preload("res://assets/art/room1_seam_contact_r6/wall_left.png"), preload("res://assets/art/room1_seam_contact_r6/wall_right.png"), preload("res://assets/art/room1_seam_contact_r6/wall_front.png"), preload("res://assets/art/room1_seam_contact_r6/wall_rear.png")]
var seam_contact_fixed := true

func _ready() -> void:
	super._ready()
	if not Engine.is_editor_hint(): set_seam_contact_fixed(true)

func set_seam_contact_fixed(enabled: bool) -> void:
	seam_contact_fixed = enabled
	var maps := CONTACT_MAPS if enabled else [WALL_LEFT, WALL_RIGHT, WALL_FRONT, WALL_REAR]
	for mesh_name in full_materials:
		if mesh_name == "Floor_continuous_no_tile_seams": continue
		for material: ShaderMaterial in full_materials[mesh_name]:
			for index in 4:
				material.set_shader_parameter(["full_wall_left_map", "full_wall_right_map", "full_wall_front_map", "full_wall_rear_map"][index], maps[index])
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_V:
		set_seam_contact_fixed(not seam_contact_fixed)
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	super._update_info()
	if info: info.text += "\nV 接缝旧化接触修正：" + ("r6 已修正" if seam_contact_fixed else "r5 旧版空边")
