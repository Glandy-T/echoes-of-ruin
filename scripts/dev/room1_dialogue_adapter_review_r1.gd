extends "res://scripts/dev/room1_sprite_player_lighting_r2.gd"

const GAME_UI := preload("res://scenes/ui/game_ui.tscn")
var review_ui: CanvasLayer
var interaction_area: Area3D
var label_anchor: Node2D
var input_locked := false
var player_near := false

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	# GameUI's existing lock interface is served by this review controller.
	add_to_group("player")
	review_ui = GAME_UI.instantiate()
	add_child(review_ui)
	label_anchor = Node2D.new()
	add_child(label_anchor)
	call_deferred("_setup_test_point")

func _setup_test_point() -> void:
	interaction_area = Area3D.new()
	interaction_area.name = "TemporaryInteractionZone"
	interaction_area.collision_layer = 0
	interaction_area.collision_mask = 2
	var shape := SphereShape3D.new()
	shape.radius = 1.25
	var collision := CollisionShape3D.new()
	collision.shape = shape
	interaction_area.add_child(collision)
	add_child(interaction_area)
	interaction_area.global_position = player.global_position + Vector3(0, 0.8, 0)
	interaction_area.body_entered.connect(_on_test_body_entered)
	interaction_area.body_exited.connect(_on_test_body_exited)

func set_input_locked(locked: bool) -> void:
	input_locked = locked
	if locked:
		player.velocity.x = 0.0
		player.velocity.z = 0.0

func _physics_process(delta: float) -> void:
	if input_locked:
		var previous_test_mode := test_mode
		var previous_test_input := test_input
		test_mode = true
		test_input = Vector2.ZERO
		super._physics_process(delta)
		test_mode = previous_test_mode
		test_input = previous_test_input
	else:
		super._physics_process(delta)

func _process(delta: float) -> void:
	super._process(delta)
	if interaction_area and label_anchor:
		label_anchor.global_position = $ReviewCamera.unproject_position(interaction_area.global_position)

func _unhandled_input(event: InputEvent) -> void:
	if player_near and event.is_action_pressed("interact") and review_ui.can_accept_world_interaction():
		var pages: Array[String] = ["これは3D調査と会話のテストです。", "会話を閉じると移動できます。"]
		review_ui.start_dialogue(pages)
		get_viewport().set_input_as_handled()

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():
		return
	super._unhandled_key_input(event)

func _on_test_body_entered(body: Node3D) -> void:
	if body != player:
		return
	player_near = true
	review_ui.show_interaction_name(interaction_area, "E：調査テスト", label_anchor, Vector2(0, -30))

func _on_test_body_exited(body: Node3D) -> void:
	if body != player:
		return
	player_near = false
	review_ui.hide_interaction_name(interaction_area)

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 交互与对话试验 r1\nWASD移动 · E调查测试 · Enter翻页 · Esc关闭/暂停\n临时测试点位于起始位置；未加入正式剧情或新设施。"
