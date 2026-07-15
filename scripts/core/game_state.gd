extends Node

# 这些状态只在当前游戏运行期间保存，不是磁盘存档。
var next_spawn_id: StringName = &"start"
var world_flags: Dictionary = {}
# Runtime preference shared by the title menu and in-game UI.
# This intentionally survives reset_demo_state(), but is not saved to disk.
var interaction_hints_enabled: bool = true


func set_flag(id: StringName, value: Variant) -> void:
	if id.is_empty():
		push_warning("GameState.set_flag() received an empty state ID.")
		return
	world_flags[id] = value


func get_flag(id: StringName, default_value: Variant = false) -> Variant:
	if id.is_empty():
		return default_value
	return world_flags.get(id, default_value)


func reset_demo_state() -> void:
	next_spawn_id = &"start"
	world_flags.clear()
