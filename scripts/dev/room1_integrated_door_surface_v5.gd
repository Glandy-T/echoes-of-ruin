extends "res://scripts/dev/room1_integrated_door_v3.gd"

# Same construction, motion, emergency-light shading and access feedback as v3.
# Only the face's pixel surface changes; no v4 bottom-light adjustment is used.
const DOOR_SURFACE_V5 := preload("res://assets/art/room1_integrated_door_surface_v5/door_front.png")


func _replace_placeholder() -> void:
	super._replace_placeholder()
	panel_material.set_shader_parameter("pixel_map", DOOR_SURFACE_V5)


func _update_info() -> void:
	super._update_info()
	if info:
		info.text = "Room 1 / 一体化门旧化分布 v5 · 审图\n仅更换门面像素图：密封边、状态窗凹边与底部窄接触痕；亮度和门体沿用 v3\nWASD移动 · F1走廊 · F2西梯 · F3一层梯间 · R回房间。"
