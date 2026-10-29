extends "res://scripts/dev/room1_complete_r19.gd"

# The formal Room 1 entry point deliberately inherits the approved review build.
# Keep its play-mode policy here so the review scene remains available as a tool.

func _ready() -> void:
	GameState.set_flag(&"room1_play_mode", true)
	# The review-route ancestor disables this for repeated tooling runs.  The
	# formal entry restores the approved opening dialogue before its deferred
	# starter is scheduled in the inherited _ready chain.
	opening_dialogue_enabled = true
	super._ready()
	if is_instance_valid(info):
		info.get_parent().hide()


func _unhandled_key_input(event: InputEvent) -> void:
	# r19 inherits several review-only shortcuts.  Do not call the inherited
	# handler during normal play: movement and dialogue use actions /
	# _unhandled_input, while this prevents F-keys and diagnostic letters from
	# changing the scene's presentation.
	if bool(GameState.get_flag(&"room1_play_mode", false)):
		return
	super._unhandled_key_input(event)
