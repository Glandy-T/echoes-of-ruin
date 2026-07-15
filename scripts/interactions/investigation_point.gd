extends Area2D

@export var prompt_text := "Eキーで調べる"
@export_multiline var pages: Array[String] = []
@export var expression_ids: Array[StringName] = []
@export var detail_texture: Texture2D

var player_near := false
var _ui: Node


func _ready() -> void:
	_ui = get_tree().get_first_node_in_group("game_ui")
	if _ui == null:
		push_warning("InvestigationPoint '%s' could not find GameUI." % name)


func _process(_delta: float) -> void:
	if not player_near or not Input.is_action_just_pressed("interact"):
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
	if _ui != null and not prompt_text.is_empty():
		_ui.call("show_prompt", self, prompt_text)


func _on_body_exited(body: Node) -> void:
	if not body.is_in_group("player"):
		return
	player_near = false
	if _ui != null:
		_ui.call("hide_prompt", self)


func _can_accept_world_interaction() -> bool:
	if _ui == null or not _ui.has_method("can_accept_world_interaction"):
		return false
	return bool(_ui.call("can_accept_world_interaction"))
