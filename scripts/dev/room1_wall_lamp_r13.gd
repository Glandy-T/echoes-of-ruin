extends "res://scripts/dev/room1_wall_pixellab_r12.gd"

const WALLS_R13 := [preload("res://assets/art/room1_wall_lamp_r13/wall_left.png"),preload("res://assets/art/room1_wall_lamp_r13/wall_right.png"),preload("res://assets/art/room1_wall_lamp_r13/wall_front.png"),preload("res://assets/art/room1_wall_lamp_r13/wall_rear.png")]
const LAMP_SHADER := preload("res://scripts/dev/room1_wall_lamp_r13.gdshader")

func _apply_portal_wall() -> void:
	# All three receiver pieces use the same current rear-wall map.
	for name in ["Wall_rear_left","Wall_rear_right","Wall_rear_door_header"]:
		for material: ShaderMaterial in full_materials.get(name,[]):
			material.set_shader_parameter("full_wall_rear_map", WALLS_R13[3] if wall_rework_on else VARIED_WALLS[3])

func set_wall_rework(enabled: bool) -> void:
	wall_rework_on=enabled
	var maps := WALLS_R13 if enabled else VARIED_WALLS
	for name in full_materials:
		if name=="Floor_continuous_no_tile_seams":continue
		for material: ShaderMaterial in full_materials[name]:
			var params:=_copy_parameters(material)
			material.shader=LAMP_SHADER if enabled else FULL_SHADER
			for key: StringName in params:material.set_shader_parameter(key,params[key])
			for i in 4:material.set_shader_parameter(["full_wall_left_map","full_wall_right_map","full_wall_front_map","full_wall_rear_map"][i],maps[i])
	_update_info()

func _enable_r5_base_color() -> void:
	diagnostic_material_snapshots.clear()
	for material: ShaderMaterial in baked_receivers:
		if material.shader!=FULL_SHADER and material.shader!=LAMP_SHADER:
			var params:=_copy_parameters(material)
			diagnostic_material_snapshots.append({"material":material,"shader":material.shader,"parameters":params})
			material.shader=FULL_SHADER
			for key: StringName in params:material.set_shader_parameter(key,params[key])
			material.set_shader_parameter("structure_enabled",0.0)
			material.set_shader_parameter("full_surface_mode",0)
		material.set_shader_parameter("base_color_preview",1.0)

func _restore_r5_base_color() -> void:
	super._restore_r5_base_color()
	for material: ShaderMaterial in baked_receivers:
		if material.shader==LAMP_SHADER:material.set_shader_parameter("base_color_preview",0.0)

func _update_info() -> void:
	super._update_info()
	if info:info.text="Room 1 / 后墙与灯带 r13\nB比较r12／r13："+("后墙统一＋灯罩像素材质" if wall_rework_on else "r12原样")+"\nN颜色诊断 · J回观察点 · WASD移动"
