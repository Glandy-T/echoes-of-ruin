@tool
extends "res://scripts/dev/room1_pixel_motion_test_r2.gd"
var left_uv_fixed := true
var fixed_left_mesh: Mesh
var previous_left_mesh: Mesh

func _ready() -> void:
	baked_geometry_path = "res://assets/art/room1_continuous_bake_r3/room1_baked_uv2_r4_uv_fixed.glb"
	super._ready()
	fixed_left_mesh = $Shell.find_child("Wall_left", true, false).mesh
	var original := (load("res://assets/art/room1_continuous_bake_r3/room1_baked_uv2_r3.glb") as PackedScene).instantiate()
	previous_left_mesh = original.find_child("Bake_Shell_Wall_left", true, false).mesh
	original.free()
	_update_info()

func set_pixel_mode(_index: int) -> void:
	# User chose the original resolution; keep older density trials separately.
	super.set_pixel_mode(0)

func apply_left_uv_state() -> void:
	$Shell.find_child("Wall_left", true, false).mesh = fixed_left_mesh if left_uv_fixed else previous_left_mesh
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	super._unhandled_key_input(event)
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F5:
		left_uv_fixed = not left_uv_fixed
		apply_left_uv_state()

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 原分辨率 · 左墙UV修正 r4 · 待审\nF5左墙修正 %s · WASD移动 · R复位 · 1–9位置\nK人物阴影 · C碰撞 · L灯带 · G舱光 · B屏幕 · H说明\n1280×720；像素感留待贴图返修。" % left_uv_fixed
