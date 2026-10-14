extends SceneTree
func _initialize() -> void:
	var room := (load("res://scenes/dev/room1_player_physics_test_r1.tscn") as PackedScene).instantiate()
	room.name = "Room1PixelResolutionTestR1"
	room.scene_file_path = ""
	room.set_script(load("res://scripts/dev/room1_pixel_resolution_test_r1.gd"))
	var scene := PackedScene.new()
	var error := scene.pack(room)
	if error == OK:
		error = ResourceSaver.save(scene, "res://scenes/dev/room1_pixel_resolution_test_r1.tscn")
	print("ROOM1_PIXEL_BUILD: ", error)
	room.free()
	quit(error)
