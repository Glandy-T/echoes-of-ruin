extends Node2D

@export var default_spawn_id: StringName = &"start"
@export var camera_left: int = 0
@export var camera_top: int = 0
@export var camera_right: int = 1797
@export var camera_bottom: int = 650


func _ready() -> void:
	call_deferred("_initialize_room")


func _initialize_room() -> void:
	var player := get_tree().get_first_node_in_group("player") as CharacterBody2D
	if player == null:
		push_error("RoomController could not find a node in the 'player' group.")
		return

	var spawn := _find_spawn(GameState.next_spawn_id)
	if spawn == null:
		push_warning(
			"Spawn point '%s' was not found in room '%s'. Trying default '%s'."
			% [GameState.next_spawn_id, name, default_spawn_id]
		)
		spawn = _find_spawn(default_spawn_id)

	if spawn != null:
		player.global_position = spawn.global_position
	else:
		push_warning("No safe spawn point was found. Keeping the Player's scene position.")

	_configure_camera(player)


func _find_spawn(spawn_id: StringName) -> Marker2D:
	for node in get_tree().get_nodes_in_group("spawn_point"):
		if (
			node is Marker2D
			and is_ancestor_of(node)
			and StringName(node.get("spawn_id")) == spawn_id
		):
			return node as Marker2D
	return null


func _configure_camera(player: CharacterBody2D) -> void:
	var camera := player.get_node_or_null("Camera2D") as Camera2D
	if camera == null:
		push_warning("RoomController could not find Player/Camera2D.")
		return

	camera.limit_left = camera_left
	camera.limit_top = camera_top
	camera.limit_right = camera_right
	camera.limit_bottom = camera_bottom
