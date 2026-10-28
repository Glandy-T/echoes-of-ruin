extends "res://scripts/dev/room1_hero_scale_review_r1.gd"

const OPEN_DISTANCE := 1.52
const OPEN_SECONDS := 3.0
const SCAN_SECONDS := 1.5
const CLOSE_DELAY := 1.0
const POD_DETAIL_TEXTURE := preload("res://assets/art/cryopod_standard_v8/cryopod_standard_v8_display.png")
var chip_enabled := true
var door_mesh: MeshInstance3D
var door_body: StaticBody3D
var door_sensor: Area3D
var door_closed_position: Vector3
var body_closed_position: Vector3
var door_fraction := 0.0
var door_occupied := false
var empty_seconds := 0.0
var door_bloom_occluder: MeshInstance3D
var scan_line: MeshInstance3D
var scan_time := 0.0
var scan_complete := false
var exit_anchor: Node2D
var exit_prompt_visible := false
@export_file("*.tscn") var destination_scene := ""
@export var opening_dialogue_enabled := true
const OPENING_FLAG := &"room1_opening_dialogue_seen"

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	door_mesh = $Shell.find_child("MAIN_DOOR_PLACEHOLDER_NOT_APPROVED", true, false) as MeshInstance3D
	door_body = get_node("Solid_MAIN_DOOR_PLACEHOLDER_NOT_APPROVED") as StaticBody3D
	door_closed_position = door_mesh.global_position
	body_closed_position = door_body.global_position
	for node in bloom_camera.get_parent().get_children():
		if node is MeshInstance3D and node.mesh == door_mesh.mesh and node.global_position.distance_to(door_closed_position) < 0.01:
			door_bloom_occluder = node
			break
	_make_sensor()
	_make_temporary_exit_boundary()
	_make_black_doorway()
	_make_scan_indicator()
	exit_anchor = Node2D.new()
	add_child(exit_anchor)
	_update_info()
	call_deferred("_start_opening_dialogue")

func _start_opening_dialogue() -> void:
	if not opening_dialogue_enabled or bool(GameState.get_flag(OPENING_FLAG, false)):
		return
	var pages: Array[String] = ["あ……頭、痛い……。", "ここは……どこ？"]
	var expressions: Array[StringName] = [&"confused", &"confused"]
	GameState.set_flag(OPENING_FLAG, true)
	review_ui.start_dialogue(pages, expressions)

func _setup_test_point() -> void:
	# Replace the inherited demo point with the protagonist's actual pod.
	interaction_area = Area3D.new()
	interaction_area.name = "OwnPodInvestigation"
	interaction_area.collision_layer = 0
	interaction_area.collision_mask = 2
	var shape := BoxShape3D.new()
	shape.size = Vector3(3.2, 2.6, 3.5)
	var collision := CollisionShape3D.new()
	collision.shape = shape
	interaction_area.add_child(collision)
	add_child(interaction_area)
	interaction_area.global_position = standard.global_position + Vector3(0, 0.8, 0)
	interaction_area.body_entered.connect(_on_test_body_entered)
	interaction_area.body_exited.connect(_on_test_body_exited)

func _on_test_body_entered(body: Node3D) -> void:
	if body != player:
		return
	player_near = true
	review_ui.show_interaction_name(interaction_area, "E：休眠ポッド", label_anchor, Vector2(0, -30))

func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed("interact") or not review_ui.can_accept_world_interaction():
		return
	if _can_use_exit():
		if destination_scene.is_empty() or not ResourceLoader.exists(destination_scene):
			review_ui.show_text("この先はまだ準備されていません。")
		else:
			get_tree().change_scene_to_file(destination_scene)
		get_viewport().set_input_as_handled()
	elif player_near:
		if not standard.screen_powered:
			review_ui.show_text("画面が消えている。")
			get_viewport().set_input_as_handled()
			return
		var pages: Array[String] = ["情報パネル……？", "グラン……私の名前、みたい。"]
		var expressions: Array[StringName] = [&"confused", &"deadpan"]
		review_ui.start_detail_dialogue(POD_DETAIL_TEXTURE, pages, expressions)
		get_viewport().set_input_as_handled()

func _can_use_exit() -> bool:
	return door_fraction >= 0.99 and absf(player.global_position.x - door_closed_position.x) < 0.9 and player.global_position.z < door_closed_position.z + 1.05

func _process(delta: float) -> void:
	super._process(delta)
	if not is_instance_valid(exit_anchor):
		return
	exit_anchor.global_position = $ReviewCamera.unproject_position(door_closed_position)
	var show := _can_use_exit()
	if show != exit_prompt_visible:
		exit_prompt_visible = show
		if show:
			review_ui.show_interaction_name(door_sensor, "E：出口", exit_anchor, Vector2(0, -35))
		else:
			review_ui.hide_interaction_name(door_sensor)

func _make_black_doorway() -> void:
	var rect := QuadMesh.new()
	rect.size = Vector2(1.37, 2.38)
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color.BLACK
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	var backdrop := MeshInstance3D.new()
	backdrop.name = "BlackDoorway"
	backdrop.mesh = rect
	backdrop.material_override = material
	backdrop.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(backdrop)
	backdrop.global_position = door_closed_position + Vector3(0, 0, -0.09)

func _make_scan_indicator() -> void:
	var rect := QuadMesh.new()
	rect.size = Vector2(0.34, 0.025)
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color(0.38, 0.66, 0.7)
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	scan_line = MeshInstance3D.new()
	scan_line.name = "TemporaryScanLine"
	scan_line.mesh = rect
	scan_line.material_override = material
	scan_line.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	scan_line.visible = false
	add_child(scan_line)

func _make_sensor() -> void:
	door_sensor = Area3D.new()
	door_sensor.name = "DoorSensorTest"
	door_sensor.collision_layer = 0
	door_sensor.collision_mask = 2
	var shape := BoxShape3D.new()
	shape.size = Vector3(2.8, 2.8, 2.8)
	var collision := CollisionShape3D.new()
	collision.shape = shape
	door_sensor.add_child(collision)
	add_child(door_sensor)
	door_sensor.global_position = door_closed_position + Vector3(0, 0, 0.85)
	door_sensor.body_entered.connect(_on_door_body_entered)
	door_sensor.body_exited.connect(_on_door_body_exited)

func _make_temporary_exit_boundary() -> void:
	# The next room does not exist yet. Prevent walking off the room floor.
	var body := StaticBody3D.new()
	body.name = "TemporaryExitBoundary"
	body.collision_layer = 1
	body.collision_mask = 2
	var shape := BoxShape3D.new()
	shape.size = Vector3(1.4, 2.4, 0.1)
	var collision := CollisionShape3D.new()
	collision.shape = shape
	body.add_child(collision)
	add_child(body)
	body.global_position = door_closed_position + Vector3(0, 0, -0.15)

func _physics_process(delta: float) -> void:
	super._physics_process(delta)
	if Engine.is_editor_hint() or not door_mesh:
		return
	if door_occupied:
		empty_seconds = 0.0
		if chip_enabled and not scan_complete:
			scan_time = minf(scan_time + delta, SCAN_SECONDS)
			scan_complete = scan_time >= SCAN_SECONDS
	else:
		empty_seconds += delta
		scan_time = 0.0
		scan_complete = false
	# Hold the door while someone is near, including if authorization changes.
	var target := door_fraction
	if door_occupied and scan_complete and chip_enabled:
		target = 1.0
	elif not door_occupied and empty_seconds >= CLOSE_DELAY:
		target = 0.0
	door_fraction = move_toward(door_fraction, target, delta / OPEN_SECONDS)
	var movement := Vector3(OPEN_DISTANCE * door_fraction, 0, 0)
	door_mesh.global_position = door_closed_position + movement
	door_body.global_position = body_closed_position + movement
	if is_instance_valid(door_bloom_occluder):
		door_bloom_occluder.global_position = door_closed_position + movement
	if scan_line:
		scan_line.visible = door_occupied and chip_enabled and not scan_complete
		scan_line.global_position = door_closed_position + movement + Vector3(0.42, lerpf(0.72, -0.72, scan_time / SCAN_SECONDS), 0.05)

func _on_door_body_entered(body: Node3D) -> void:
	if body == player:
		door_occupied = true

func _on_door_body_exited(body: Node3D) -> void:
	if body == player:
		door_occupied = false

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_0:
		teleport_player(Vector3(10.5, 0.05, -6.8))
		get_viewport().set_input_as_handled()
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_U:
		chip_enabled = not chip_enabled
		if not chip_enabled and door_fraction <= 0.0:
			scan_time = 0.0
			scan_complete = false
		_update_info()
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 主门和台词试验\n0到门前 · WASD移动 · U切换测试芯片（%s） · E调查/出口 · Enter翻页\n扫描后慢速开门，门后为黑色；下一区域尚未接入。" % ("开启" if chip_enabled else "关闭")

