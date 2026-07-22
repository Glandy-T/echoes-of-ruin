extends Area2D

@export var display_name: String = ""
@export var label_offset := Vector2(0, -64)
@export_multiline var pages: Array[String] = []
@export var expression_ids: Array[StringName] = []
@export var detail_texture: Texture2D
@export var available_flag_id: StringName = &""
@export var available_flag_value := true

var player_near := false
var _ui: Node
var _interaction_name_visible := false


func _ready() -> void:
	_ui = get_tree().get_first_node_in_group("game_ui")
	if _ui == null:
		push_warning("InvestigationPoint '%s' could not find GameUI." % name)


func _process(_delta: float) -> void:
	_update_interaction_name()
	if not player_near or not _is_available() or not Input.is_action_just_pressed("interact"):
		return
	if not _can_accept_world_interaction():
		return
	_start_investigation()


func _start_investigation() -> void:
	if _ui == null or pages.is_empty():
		return
	if detail_texture == null:
		_ui.call("start_dialogue", pages, expression_ids)
	else:
		_ui.call("start_detail_dialogue", detail_texture, pages, expression_ids)


func _on_body_entered(body: Node) -> void:
	if not body.is_in_group("player"):
		return
	player_near = true
	_update_interaction_name()


func _on_body_exited(body: Node) -> void:
	if not body.is_in_group("player"):
		return
	player_near = false
	_update_interaction_name()


func _is_available() -> bool:
	if available_flag_id.is_empty():
		return true
	return bool(GameState.get_flag(available_flag_id, false)) == available_flag_value


func _update_interaction_name() -> void:
	var should_show := (
		player_near
		and _is_available()
		and _ui != null
		and not display_name.is_empty()
	)
	if should_show == _interaction_name_visible:
		return

	_interaction_name_visible = should_show
	if should_show:
		_ui.call("show_interaction_name", self, display_name, self, label_offset)
	else:
		_ui.call("hide_interaction_name", self)


func _can_accept_world_interaction() -> bool:
	if _ui == null or not _ui.has_method("can_accept_world_interaction"):
		return false
	return bool(_ui.call("can_accept_world_interaction"))
