@tool
extends "res://scripts/dev/room1_pod_exit_animation_r2.gd"

func _window_effect_pods() -> PackedStringArray:
	return PackedStringArray(["P02", "P12", "P17"])

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 三亮仓统一玻璃与舱内光 r3\nR重播 · 空格跳过 · 出仓后WASD移动 · G舱光 · H说明\nP12主角仓打开，P02/P17红屏；三仓使用相同透光材质。\n胶囊占位动作预演；像素反光保留，玻璃接缝待后续。"
