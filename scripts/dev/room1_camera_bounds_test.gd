@tool
extends "res://scripts/dev/room1_camera_follow_test.gd"

## Boundary experiment for the existing fixed-angle perspective camera.
@export var minimum_camera_z_m := 1.0
@export var maximum_camera_z_m := 4.54
const SHADOW_ONLY_NAMES := ["Wall_front", "Roof_hidden_for_cutaway"]
const EDGE_POSITIONS := [Vector3(10.5, 0, -4.75), Vector3(0.55, 0, -4.75), Vector3(20.45, 0, -4.75), Vector3(10.5, 0, -0.55), Vector3(10.5, 0, -8.95), Vector3(0.55, 0, -0.55), Vector3(20.45, 0, -0.55), Vector3(0.55, 0, -8.95), Vector3(20.45, 0, -8.95)]

func _ready() -> void:
	super._ready()
	# Restore the side walls. Only the front wall and ceiling disappear from the camera.
	var left := $Shell.find_child("Wall_left", true, false) as MeshInstance3D
	left.visible = true
	left.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for node_name: String in SHADOW_ONLY_NAMES:
		var object := $Shell.find_child(node_name, true, false) as MeshInstance3D
		object.visible = true
		object.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	_update_info()

func update_follow_camera() -> void:
	var target := $FollowTarget as Node3D
	var camera := $ReviewCamera as Camera3D
	var camera_z := clampf(target.position.z + camera_distance_m, minimum_camera_z_m, maximum_camera_z_m)
	# Perspective width changes with depth. Use the marker's upper extent so its
	# whole silhouette stays inside the frame, including at the front corners.
	var head := Vector3(target.position.x, 1.65, target.position.z)
	var centered_camera := Vector3(target.position.x, camera_height_m, camera_z)
	var head_depth := locked_basis.z.dot(centered_camera - head)
	var half_width := head_depth * tan(deg_to_rad(horizontal_fov_degrees) * 0.5)
	var horizontal_margin := maxf(half_width * 0.9, 0.5)
	var camera_x := clampf(target.position.x, 0.2 + horizontal_margin, 20.8 - horizontal_margin)
	camera.position = Vector3(camera_x, camera_height_m, camera_z)
	camera.basis = locked_basis

func _unhandled_key_input(event: InputEvent) -> void:
	super._unhandled_key_input(event)
	if Engine.is_editor_hint() or not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.physical_keycode >= KEY_1 and event.physical_keycode <= KEY_9:
		$FollowTarget.position = EDGE_POSITIONS[event.physical_keycode - KEY_1]
		update_follow_camera()
		_update_info()

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 镜头边界试验 · 角度/高度固定\nWASD 移动 · R复位 · T标记 · H说明\n1中央 2左 3右 4前 5后 · 6–9四角\n靠边时镜头停下，目标离开中心；前墙/屋顶只投影。\n比例标记无碰撞；舱体遮挡仍需后续审查。"
