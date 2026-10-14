extends SceneTree
func _initialize() -> void:
	var room := (load("res://scenes/dev/room1_pixel_motion_test_r2.tscn") as PackedScene).instantiate()
	room.name = "Room1LeftWallUVReviewR4"
	room.scene_file_path = ""
	room.set_script(load("res://scripts/dev/room1_left_wall_uv_review_r4.gd"))
	var scene := PackedScene.new()
	var error := scene.pack(room)
	if error == OK:
		error = ResourceSaver.save(scene, "res://scenes/dev/room1_left_wall_uv_review_r4.tscn")
	print("ROOM1_LEFT_UV_BUILD: ", error)
	room.free()
	quit(error)
