extends "res://scripts/dev/cryo_building_room1_route_v3.gd"

# Door art and feedback review on the already verified Room 1 -> 4F route.
# Single authorized actor: no second-person/tailgating simulation in this scene.
const DOOR_SCENE := preload("res://assets/art/room1_integrated_door_v3/room1_integrated_door_v3.glb")
const DOOR_PIXELS := preload("res://assets/art/room1_integrated_door_v3/door_front.png")
const FRONT_SHADER := preload("res://scripts/dev/room1_integrated_door_v3.gdshader")

var integrated_root: Node3D
var status_window: MeshInstance3D
var status_material: StandardMaterial3D
var frame_material: StandardMaterial3D
var panel_material: ShaderMaterial
var pass_valid := false
var feedback_state := "idle"


func _apply_review_materials() -> void:
	super._apply_review_materials()
	# The inherited route is an intentionally bright identification greybox.
	# Only this door art-review scene needs a dark 4F entry preview so opening
	# the leaf does not reveal a bright rectangle in the emergency-lit room.
	# This is not a final corridor lighting or material decision.
	var route := get_node(EXTERNAL_ROUTE) as Node3D
	var entry_wall := _review_material(Color(0.080, 0.105, 0.105))
	var entry_floor := _review_material(Color(0.060, 0.080, 0.080))
	var opposite_door := _review_material(Color(0.115, 0.145, 0.150))
	for mesh: MeshInstance3D in route.find_children("*", "MeshInstance3D", true, false):
		var name_text := str(mesh.name)
		if name_text.begins_with("R4F_4F_W"):
			mesh.material_override = entry_wall
		elif name_text.begins_with("R4F_4F_FloorCell"):
			mesh.material_override = entry_floor
		elif name_text.begins_with("R4F_4F_D") and "LockedDoor" in name_text:
			mesh.material_override = opposite_door


func _make_scan_indicator() -> void:
	# The old full-door scan line contradicts the integrated-window brief.
	pass


func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	_replace_placeholder()
	_update_feedback()
	_update_info()


func _replace_placeholder() -> void:
	var previous_mesh := door_mesh
	var previous_body := door_body
	previous_mesh.visible = false
	previous_body.collision_layer = 0
	previous_body.collision_mask = 0
	if is_instance_valid(door_bloom_occluder):
		door_bloom_occluder.visible = false

	integrated_root = DOOR_SCENE.instantiate() as Node3D
	integrated_root.name = "IntegratedDoorV3"
	add_child(integrated_root)
	integrated_root.global_position = door_closed_position
	var panel := integrated_root.find_child("DoorPanel", true, false) as MeshInstance3D
	assert(panel != null and panel.mesh != null)
	panel_material = ShaderMaterial.new()
	panel_material.shader = FRONT_SHADER
	panel_material.set_shader_parameter("pixel_map", DOOR_PIXELS)
	panel.set_surface_override_material(0, panel_material)
	# The leaf's narrow sides are a dark in-wall seal, not a lit metal applique.
	panel.set_surface_override_material(1, _unshaded_color(Color(0.006, 0.012, 0.012)))
	door_mesh = panel
	door_closed_position = panel.global_position

	var body := StaticBody3D.new()
	body.name = "IntegratedDoorSolidV3"
	body.collision_layer = 1
	body.collision_mask = 2
	add_child(body)
	body.global_position = door_closed_position
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1.37, 2.30, 0.085)
	shape.shape = box
	body.add_child(shape)
	door_body = body
	body_closed_position = body.global_position

	status_window = MeshInstance3D.new()
	status_window.name = "EyeHeightStatusWindow"
	var status_quad := QuadMesh.new()
	status_quad.size = Vector2(0.115, 0.045)
	status_window.mesh = status_quad
	status_window.position = Vector3(0, 0.318, 0.052)
	status_window.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	status_material = _unshaded_color(Color(0.025, 0.045, 0.05))
	status_window.material_override = status_material
	panel.add_child(status_window)

	frame_material = _unshaded_color(Color(0.008, 0.014, 0.014))
	for part: MeshInstance3D in integrated_root.find_children("JambLight_*", "MeshInstance3D", true, false):
		part.material_override = frame_material
		part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	assert(integrated_root.find_children("JambLight_*", "MeshInstance3D", true, false).size() == 4)


func _unshaded_color(color: Color) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.albedo_color = color
	return material


func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	if not is_instance_valid(status_material):
		return
	if door_occupied and scan_complete and chip_enabled:
		pass_valid = true
	if not door_occupied and door_fraction <= 0.005:
		pass_valid = false
	_update_feedback()


func _process(delta: float) -> void:
	super._process(delta)
	if is_instance_valid(panel_material):
		panel_material.set_shader_parameter("strip_on", 1.0 if strip_on else 0.0)
	if is_instance_valid(status_material):
		_update_feedback()


func _update_feedback() -> void:
	if not is_instance_valid(status_material) or not is_instance_valid(frame_material):
		return
	var new_state := "idle"
	var status_color := Color(0.025, 0.045, 0.05)
	if pass_valid and door_fraction > 0.005:
		new_state = "pass"
		status_color = Color(0.29, 0.67, 0.45)
	elif door_occupied and not chip_enabled:
		new_state = "denied"
		status_color = Color(0.66, 0.20, 0.16)
	elif door_occupied and chip_enabled and not scan_complete:
		new_state = "scanning"
		var flash := fmod(float(Time.get_ticks_msec()) / 1000.0, 0.5) < 0.30
		status_color = Color(0.69, 0.50, 0.19) if flash else Color(0.18, 0.15, 0.08)
	elif pass_valid:
		new_state = "pass"
		status_color = Color(0.29, 0.67, 0.45)
	feedback_state = new_state
	status_material.albedo_color = status_color
	# One continuous inner-jamb ring glows green only during valid passage.
	# The one-actor review has no red jamb state and does not simulate tailgating.
	frame_material.albedo_color = Color(0.22, 0.55, 0.38) if new_state == "pass" else Color(0.008, 0.014, 0.014)


func _update_info() -> void:
	if info:
		info.text = "Room 1 / 一体化门与像素表面 v3 · 审图\n靠近自动认证：小窗黄闪 → 绿灯＋门框内侧一圈绿灯 → 复位；U切换测试芯片可见小窗红色拒绝\nWASD移动 · F1走廊 · F2西梯 · F3一层梯间 · R回房间。红色门框与第二人尾随未制作。"
