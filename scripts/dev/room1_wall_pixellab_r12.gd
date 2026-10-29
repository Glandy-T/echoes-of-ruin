extends "res://scripts/dev/room1_wall_pixellab_r11.gd"

const VARIED_WALLS := [preload("res://assets/art/room1_wall_pixellab_r12/wall_left.png"), preload("res://assets/art/room1_wall_pixellab_r12/wall_right.png"), preload("res://assets/art/room1_wall_pixellab_r12/wall_front.png"), preload("res://assets/art/room1_wall_pixellab_r12/wall_rear.png")]

func set_wall_rework(enabled: bool) -> void:
	wall_rework_on = enabled
	var maps := VARIED_WALLS if enabled else NEW_WALLS
	for name in full_materials:
		if name == "Floor_continuous_no_tile_seams": continue
		for material: ShaderMaterial in full_materials[name]:
			for i in 4:
				material.set_shader_parameter(["full_wall_left_map", "full_wall_right_map", "full_wall_front_map", "full_wall_rear_map"][i], maps[i])
	_update_info()

func _update_info() -> void:
	super._update_info()
	if info:
		info.text = "Room 1 / 四墙 PixelLab 差分 r12\nB 比较r11／r12：" + ("16种墙板安排" if wall_rework_on else "r11原安排") + "\nN颜色诊断 · J回观察点 · WASD移动"
