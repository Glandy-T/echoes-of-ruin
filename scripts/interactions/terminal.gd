extends Area2D

@export var target_door_path: NodePath
@export var state_id: StringName = &""
@export var prompt_text := "Eキーで調べる"
@export_multiline var activation_text := ""
@export_multiline var already_used_text := ""
@export_multiline var failure_text := ""

var player_near := false
var used := false
var _door: Node
var _ui: Node


func _ready() -> void:
	_ui = get_tree().get_first_node_in_group("game_ui")
	if _ui == null:
		push_warning("Terminal '%s' could not find GameUI." % name)

	if target_door_path == NodePath(""):
		push_warning("Terminal '%s' has no target_door_path." % name)
	else:
		_door = get_node_or_null(target_door_path)
		if _door == null:
			push_warning("Terminal '%s' could not find target Door at '%s'." % [name, target_door_path])
		elif not _door.has_method("unlock_and_open"):
			push_warning("Terminal '%s' target does not implement unlock_and_open()." % name)
			_door = null

	used = bool(GameState.get_flag(state_id, false))


func _process(_delta: float) -> void:
	if player_near and Input.is_action_just_pressed("interact"):
		_activate()


func _activate() -> void:
	if used:
		_show_text(already_used_text)
		return

	if _door == null:
		push_warning("Terminal '%s' cannot activate because its Door target is invalid." % name)
		_show_text(failure_text)
		return

	used = true
	if not state_id.is_empty():
		GameState.set_flag(state_id, true)
	_show_text(activation_text)
	_door.call("unlock_and_open")


func _on_body_entered(body: Node) -> void:
	if not body.is_in_group("player"):
		return
	player_near = true
	if _ui != null and not prompt_text.is_empty():
		_ui.call("show_prompt", self, prompt_text)


func _on_body_exited(body: Node) -> void:
	if not body.is_in_group("player"):
		return
	player_near = false
	if _ui != null:
		_ui.call("hide_prompt", self)


func _show_text(text: String) -> void:
	if _ui != null and not text.is_empty():
		_ui.call("show_text", text)
