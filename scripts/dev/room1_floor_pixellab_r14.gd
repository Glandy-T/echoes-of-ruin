extends "res://scripts/dev/room1_wall_lamp_r13.gd"

const PIXEL_FLOOR_AGED := preload("res://assets/art/room1_floor_pixellab_r14/floor_aged.png")
const PIXEL_FLOOR_LEAKS := preload("res://assets/art/room1_floor_pixellab_r14/floor_with_leaks.png")

func set_floor_contact(enabled: bool) -> void:
	floor_contact_enabled = enabled
	for material: ShaderMaterial in full_materials.get("Floor_continuous_no_tile_seams", []):
		material.set_shader_parameter("full_floor_aged_map", PIXEL_FLOOR_AGED if enabled else NEUTRAL_FLOOR_AGED)
		material.set_shader_parameter("full_floor_leaks_map", PIXEL_FLOOR_LEAKS if enabled else NEUTRAL_FLOOR_LEAKS)
	_update_info()

func _update_info() -> void:
	if info:
		info.text="Room 1 / PixelLab地坪 r14\nF 地坪比较："+("PixelLab新图" if floor_contact_enabled else "r9旧图")+"\nN原色诊断 · J回观察点 · WASD移动 · 墙面灯带保持r13"
