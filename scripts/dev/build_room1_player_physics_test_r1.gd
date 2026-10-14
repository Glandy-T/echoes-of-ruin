extends SceneTree
func _initialize() -> void:
	var room := (load("res://scenes/dev/room1_lighting_continuous_bake_r3.tscn") as PackedScene).instantiate()
	room.name = "Room1PlayerPhysicsTestR1"
	room.scene_file_path = ""
	room.set_script(load("res://scripts/dev/room1_player_physics_test_r1.gd"))
	var scene := PackedScene.new()
	var error := scene.pack(room)
	if error == OK:
		error = ResourceSaver.save(scene, "res://scenes/dev/room1_player_physics_test_r1.tscn")
	print("ROOM1_PHYSICS_BUILD: ", error)
	room.free()
	quit(error)
