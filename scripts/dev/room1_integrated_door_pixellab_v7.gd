extends "res://scripts/dev/room1_integrated_door_finish_v6.gd"

const PIXELLAB_DOOR_V7 := preload("res://assets/art/room1_integrated_door_pixellab_v7/door_front.png")


func _replace_placeholder() -> void:
	super._replace_placeholder()
	panel_material.set_shader_parameter("pixel_map", PIXELLAB_DOOR_V7)


func _update_info() -> void:
	super._update_info()
	if info:
		info.text = "Room 1 / PixelLab 门面像素 v7 · 审图\n保留 v6 结构与灯语；本版材质细节由 PixelLab 生成\nWASD移动 · F1走廊 · F2西梯 · F3一层梯间 · R回房间。"
