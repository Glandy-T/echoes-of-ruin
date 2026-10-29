extends "res://scripts/dev/room1_door_sensor_review_r1.gd"

# Independent greybox route review. Existing Room 1 scene and main game entry
# remain untouched; this child scene only supplies the corridor and stair.
const EXTERNAL_ROUTE := "OutsideRoute"
const ROUTE_COLLISION_NAMES := ["FloorCell", "_W", "LockedDoor", "EntryLanding", "TurnLanding", "Slope", "Threshold"]
var route_bodies: Array[StaticBody3D] = []


func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	# The old review scene blocked the doorway because it had no next area.
	# Keep its chip-aware sliding placeholder, but expose the new corridor.
	var old_stop := get_node_or_null("TemporaryExitBoundary") as StaticBody3D
	if old_stop:
		old_stop.collision_layer = 0
		old_stop.queue_free()
	var old_black := get_node_or_null("BlackDoorway") as MeshInstance3D
	if old_black:
		old_black.visible = false
	_apply_review_materials()
	_build_route_collision()
	_update_info()


func _apply_review_materials() -> void:
	# This is an architectural visibility pass, not a lighting decision for the stair.
	# Room 1 retains its approved textured/baked look; only the new greybox route
	# receives unshaded identification tones so it remains legible in the dark.
	var route := get_node(EXTERNAL_ROUTE) as Node3D
	var floor_material := _review_material(Color(0.25, 0.30, 0.32))
	var wall_material := _review_material(Color(0.36, 0.39, 0.40))
	var stair_material := _review_material(Color(0.43, 0.47, 0.48))
	var tread_material := _review_material(Color(0.22, 0.27, 0.29))
	var door_material := _review_material(Color(0.20, 0.26, 0.29))
	for mesh: MeshInstance3D in route.find_children("*", "MeshInstance3D", true, false):
		var name_text := str(mesh.name)
		if "LockedDoor" in name_text:
			mesh.material_override = door_material
		elif "Tread" in name_text:
			mesh.material_override = tread_material
		elif "Stair" in name_text or "Landing" in name_text or "Slope" in name_text:
			mesh.material_override = stair_material
		elif "Wall" in name_text or "_W" in name_text:
			mesh.material_override = wall_material
		else:
			mesh.material_override = floor_material


func _review_material(color: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = color
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	return material


func _build_route_collision() -> void:
	var route := get_node(EXTERNAL_ROUTE) as Node3D
	for mesh in route.find_children("*", "MeshInstance3D", true, false):
		var name_text := str(mesh.name)
		if mesh.mesh == null or "Tread" in name_text:
			continue # Visual treads ride over continuous 30-degree collision slopes.
		var relevant := false
		for fragment in ROUTE_COLLISION_NAMES:
			if fragment in name_text:
				relevant = true
				break
		if not relevant:
			continue
		var body := StaticBody3D.new()
		body.name = "RouteCollision_" + name_text
		body.collision_layer = 1
		body.collision_mask = 2
		mesh.add_child(body)
		var shape := CollisionShape3D.new()
		shape.shape = mesh.mesh.create_trimesh_shape()
		body.add_child(shape)
		route_bodies.append(body)


func update_follow_camera() -> void:
	# Room 1's original camera clamps to the room bounds. Keep its viewing
	# direction and FOV through the corridor. In the stair shaft the room's
	# eight-metre camera offset looks through solid lower-floor walls, so use
	# a provisional near follow view there. The final stair camera is undecided.
	if not has_node("FollowTarget") or not has_node("ReviewCamera"):
		return
	var target := $FollowTarget as Node3D
	var camera := $ReviewCamera as Camera3D
	var room_offset := Vector3(0, camera_height_m, camera_distance_m)
	var shaft_offset := Vector3(0, 3.6, 2.3)
	var shaft_blend := clampf((-target.position.z - 36.2) / 1.8, 0.0, 1.0)
	shaft_blend = shaft_blend * shaft_blend * (3.0 - 2.0 * shaft_blend)
	camera.position = target.position + room_offset.lerp(shaft_offset, shaft_blend)
	camera.look_at(target.position + Vector3(0, focus_height_m, 0), Vector3.UP)


func _can_use_exit() -> bool:
	# In this review, walking through the opened door is the transition. The
	# old E-to-change-scene prompt would send the player to no destination.
	return false


func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and not Engine.is_editor_hint():
		match event.physical_keycode:
			KEY_F1:
				teleport_player(Vector3(10.5, 0.05, -10.8))
				get_viewport().set_input_as_handled()
				return
			KEY_F2:
				teleport_player(Vector3(-1.5, 0.05, -36.5))
				get_viewport().set_input_as_handled()
				return
			KEY_F3:
				teleport_player(Vector3(-1.5, -11.35, -38.9))
				get_viewport().set_input_as_handled()
				return
	super._unhandled_key_input(event)


func _update_info() -> void:
	if info:
		info.text = "Room 1 → 4F西梯 → 1F梯间 / 灰模通行验证\nWASD移动 · 靠近门等待扫描开门 · F1走廊 · F2西梯入口 · F3一层梯间\nU切换测试芯片 · R回房间 · H隐藏说明。1F室外出口尚未确定。"
