extends Area2D

@export_file("*.tscn") var target_scene_path := ""
@export var target_spawn_id: StringName = &"start"
@export var prompt_text := "Eキーで移動する"
@export var required_flag_id: StringName = &""
@export var required_flag_value := true
@export_multiline var unavailable_text := ""

var player_near := false
var _ui: Node


func _ready() -> void:
	_ui = get_tree().get_first_node_in_group("game_ui")
	if _ui == null:
		push_warning("SceneExit '%s' could not find GameUI." % name)
	if target_scene_path.is_empty():
		push_warning("SceneExit '%s' has no target_scene_path." % name)
	elif not ResourceLoader.exists(target_scene_path):
		push_warning("SceneExit '%s' target scene does not exist: %s" % [name, target_scene_path])


func _process(_delta: float) -> void:
	if player_near and Input.is_action_just_pressed("interact"):
		_try_change_scene()


func _try_change_scene() -> void:
	if not required_flag_id.is_empty():
		var current_value := bool(GameState.get_flag(required_flag_id, false))
		if current_value != required_flag_value:
			if _ui != null and not unavailable_text.is_empty():
				_ui.call("show_text", unavailable_text)
			return

	if target_scene_path.is_empty() or not ResourceLoader.exists(target_scene_path):
		push_warning("SceneExit '%s' cannot change scene because the target is invalid." % name)
		return

	GameState.next_spawn_id = target_spawn_id
	var error := get_tree().change_scene_to_file(target_scene_path)
	if error != OK:
		push_error("SceneExit '%s' failed to change scene. Error: %s" % [name, error])


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
