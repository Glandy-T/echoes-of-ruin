extends Node3D

# Static import and alignment review. It does not implement player movement,
# chip permissions, stair navigation, or the unresolved 1F external exit.
func _ready() -> void:
	$Camera3D.look_at(Vector3(-71.0, 11.4, 25.0), Vector3.UP)
