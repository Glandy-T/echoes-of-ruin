extends SceneTree

func _initialize() -> void:call_deferred("run")

func run() -> void:
	for path in ["res://scripts/dev/room1_complete_r19.gd","res://scripts/areas/military_facility/cryo_room_4f_01_3d.gd"]:
		var script:=load(path) as Script
		assert(script and script.can_instantiate(),path)
	print("R19_SCRIPT_PARSE_PASS_WITH_PROJECT_AUTOLOADS")
	quit()
