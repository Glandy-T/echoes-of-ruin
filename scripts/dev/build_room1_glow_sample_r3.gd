extends SceneTree

func _initialize() -> void:
	var room := (load("res://scenes/dev/room1_glow_sample_r2.tscn") as PackedScene).instantiate()
	room.name = "Room1GlowSampleR3"
	room.scene_file_path = ""
	room.set_script(load("res://scripts/dev/room1_glow_sample_r3.gd"))
	var scene := PackedScene.new()
	var error := scene.pack(room)
	if error == OK:
		error = ResourceSaver.save(scene, "res://scenes/dev/room1_glow_sample_r3.tscn")
	print("ROOM1_GLOW_R3_BUILD: ", error)
	room.free()
	quit(error)
