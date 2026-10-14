@tool
extends Node3D

## Camera-only experiment. FollowTarget is a movable scale marker, not a character controller.
@export var camera_height_m := 2.2
@export var camera_distance_m := 8.0
@export var focus_height_m := 0.825
@export var horizontal_fov_degrees := 50.0
@export var marker_speed_m_s := 2.0

const START := Vector3(10.5, 0, -4.75)
const CUTAWAY_NAMES := ["Wall_front", "Wall_left", "Roof_hidden_for_cutaway"]
var locked_basis := Basis.IDENTITY
var info: Label

func _ready() -> void:
	for node_name: String in CUTAWAY_NAMES:
		var object := $Shell.find_child(node_name, true, false) as Node3D
		if object:
			object.visible = false
	var camera := $ReviewCamera as Camera3D
	camera.projection = Camera3D.PROJECTION_PERSPECTIVE
	camera.keep_aspect = Camera3D.KEEP_WIDTH
	camera.fov = horizontal_fov_degrees
	locked_basis = Basis.looking_at(Vector3(0, focus_height_m - camera_height_m, -camera_distance_m))
	camera.basis = locked_basis
	update_follow_camera()
	if not Engine.is_editor_hint():
		var overlay := CanvasLayer.new()
		add_child(overlay)
		var panel := PanelContainer.new()
		panel.position = Vector2(12, 12)
		panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		overlay.add_child(panel)
		info = Label.new()
		info.add_theme_font_size_override("font_size", 14)
		panel.add_child(info)
		_update_info()

func _process(delta: float) -> void:
	if Engine.is_editor_hint():
		return
	var movement := Vector2(
		float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),
		float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
	move_marker(movement, delta)
	_update_info()

func move_marker(direction: Vector2, delta: float) -> void:
	var movement := direction.limit_length() * marker_speed_m_s * delta
	$FollowTarget.position.x = clampf($FollowTarget.position.x + movement.x, 0.55, 20.45)
	$FollowTarget.position.z = clampf($FollowTarget.position.z + movement.y, -8.95, -0.55)
	update_follow_camera()

func update_follow_camera() -> void:
	# No parented camera: target Y and rotation never affect camera height or orientation.
	$ReviewCamera.position = Vector3($FollowTarget.position.x, camera_height_m, $FollowTarget.position.z + camera_distance_m)
	$ReviewCamera.basis = locked_basis

func _unhandled_key_input(event: InputEvent) -> void:
	if Engine.is_editor_hint() or not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_R:
			$FollowTarget.position = START
			update_follow_camera()
		KEY_T: $FollowTarget/ScaleMarker.visible = not $FollowTarget/ScaleMarker.visible
		KEY_H: info.get_parent().visible = not info.get_parent().visible

func _update_info() -> void:
	if info:
		var pitch := rad_to_deg(atan2(camera_height_m - focus_height_m, camera_distance_m))
		info.text = "Room 1 / 固定角度跟随镜头 · 摄像机测试\nWASD / 方向键 移动比例标记 · R 复位 · T 隐藏标记 · H 隐藏说明\n俯角 %.1f° | 高度 %.2fm | 距离 %.2fm | 水平视角 %.0f°\n仅跟随左右/前后；高度与旋转锁定。标记无碰撞，非主角模型。" % [pitch, camera_height_m, camera_distance_m, horizontal_fov_degrees]
