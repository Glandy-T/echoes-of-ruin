extends Node2D

@export var state_id: StringName = &""
@export var open_offset: Vector2 = Vector2(0, -180)
@export_range(0.0, 10.0, 0.05) var animation_time: float = 1.0

@onready var door_panel: Control = $DoorPanel
@onready var blocker: CollisionShape2D = $StaticBody2D/CollisionShape2D

var unlocked := false
var opened := false
var _closed_position := Vector2.ZERO


func _ready() -> void:
	_closed_position = door_panel.position
	if state_id.is_empty():
		push_warning("Door '%s' has no state_id and will not persist between rooms." % name)

	if bool(GameState.get_flag(state_id, false)):
		unlocked = true
		opened = true
		_apply_open_state_immediately()


func unlock() -> void:
	unlocked = true


func open() -> void:
	if opened:
		return
	if not unlocked:
		push_warning("Door '%s' cannot open before unlock()." % name)
		return

	opened = true
	if not state_id.is_empty():
		GameState.set_flag(state_id, true)

	blocker.set_deferred("disabled", true)
	var tween := create_tween()
	tween.tween_property(door_panel, "position", _closed_position + open_offset, animation_time)


func unlock_and_open() -> void:
	unlock()
	open()


func _apply_open_state_immediately() -> void:
	door_panel.position = _closed_position + open_offset
	blocker.disabled = true
