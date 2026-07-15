extends Marker2D

@export var spawn_id: StringName = &"start"


func _enter_tree() -> void:
	add_to_group("spawn_point")
