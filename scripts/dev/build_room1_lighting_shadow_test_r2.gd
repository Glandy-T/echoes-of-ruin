extends SceneTree

func _initialize() -> void:
	var room := (load("res://scenes/dev/room1_lighting_test_r1.tscn") as PackedScene).instantiate()
	room.name = "Room1LightingShadowTestR2"
	room.scene_file_path = ""
	room.set_script(load("res://scripts/dev/room1_lighting_shadow_test_r2.gd"))
	var scene := PackedScene.new()
	var error := scene.pack(room)
	if error == OK:
		error = ResourceSaver.save(scene, "res://scenes/dev/room1_lighting_shadow_test_r2.tscn")
	print("ROOM1_LIGHTING_SHADOW_R2_BUILD: ", error)
	room.free()
	quit(error)
