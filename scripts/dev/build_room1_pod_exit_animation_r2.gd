extends SceneTree
func _initialize() -> void:
	var room := (load("res://scenes/dev/room1_pod_exit_animation_r1.tscn") as PackedScene).instantiate()
	room.name = "Room1PodExitAnimationR2"
	room.scene_file_path = ""
	room.set_script(load("res://scripts/dev/room1_pod_exit_animation_r2.gd"))
	var scene := PackedScene.new()
	var error := scene.pack(room)
	if error == OK:
		error = ResourceSaver.save(scene, "res://scenes/dev/room1_pod_exit_animation_r2.tscn")
	print("ROOM1_EXIT_BUILD: ", error)
	room.free()
	quit(error)
