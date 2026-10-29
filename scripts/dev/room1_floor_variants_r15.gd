extends "res://scripts/dev/room1_floor_pixellab_r14.gd"

const VARIED_FLOOR_AGED := preload("res://assets/art/room1_floor_variants_r15/floor_aged.png")
const VARIED_FLOOR_LEAKS := preload("res://assets/art/room1_floor_variants_r15/floor_with_leaks.png")

func set_floor_contact(enabled: bool) -> void:
	floor_contact_enabled=enabled
	for material: ShaderMaterial in full_materials.get("Floor_continuous_no_tile_seams",[]):
		material.set_shader_parameter("full_floor_aged_map",VARIED_FLOOR_AGED if enabled else PIXEL_FLOOR_AGED)
		material.set_shader_parameter("full_floor_leaks_map",VARIED_FLOOR_LEAKS if enabled else PIXEL_FLOOR_LEAKS)
	_update_info()

func _update_info() -> void:
	if info:
		info.text="Room 1 / PixelLab地坪差分 r15\nF 对比："+("多原图差分铺设" if floor_contact_enabled else "r14重复底材")+"\nN原色诊断 · J回观察点 · WASD移动 · 房间与灯光保持"
