@tool
extends "res://scripts/dev/room1_pixel_resolution_test_r1.gd"

var motion_smoothing := true
var previous_physics_position := Vector3.ZERO
var current_physics_position := Vector3.ZERO
var motion_history_ready := false
var displayed_position := Vector3.ZERO

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	_reset_motion_history()
	set_pixel_mode(0)

func _reset_motion_history() -> void:
	if player:
		previous_physics_position = player.global_position
		current_physics_position = player.global_position
		displayed_position = player.global_position
		motion_history_ready = true

func teleport_player(point: Vector3) -> void:
	super.teleport_player(point)
	_reset_motion_history()

func _physics_process(delta: float) -> void:
	if motion_history_ready:
		previous_physics_position = current_physics_position
	super._physics_process(delta)
	if physics_ready:
		current_physics_position = player.global_position

func _process(delta: float) -> void:
	if motion_history_ready:
		var fraction := Engine.get_physics_interpolation_fraction()
		displayed_position = previous_physics_position.lerp(current_physics_position, fraction) if motion_smoothing else current_physics_position
		actor_mesh.global_position = displayed_position + Vector3(0, 0.825, 0)
		$FollowTarget.position = displayed_position
		update_follow_camera()
		for material in baked_receivers:
			material.set_shader_parameter("actor_feet", displayed_position)
	super._process(delta)

func _unhandled_key_input(event: InputEvent) -> void:
	super._unhandled_key_input(event)
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F4:
		motion_smoothing = not motion_smoothing
		_update_info()

func _update_info() -> void:
	if info:
		var size: Vector2i = PIXEL_SIZES[pixel_mode]
		info.text = "Room 1 / 移动同步 r2 · 待审\nF1原画 · F2中像素 · F3粗像素 · F4移动插值 %s\n当前 %d×%d；低分辨率透视细线仍可能闪动\nWASD移动 · R复位 · K阴影 · C碰撞 · H说明" % [motion_smoothing, size.x, size.y]
