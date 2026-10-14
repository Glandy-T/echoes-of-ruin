extends SceneTree

func _initialize() -> void:
	var room := (load("res://scenes/dev/room1_import_review_r1.tscn") as PackedScene).instantiate() as Node3D
	room.name = "Room1CameraFollowTest"
	room.scene_file_path = ""
	room.set_script(load("res://scripts/dev/room1_camera_follow_test.gd"))
	var target := Node3D.new()
	target.name = "FollowTarget"
	target.position = Vector3(10.5, 0, -4.75)
	room.add_child(target)
	target.owner = room
	var marker := MeshInstance3D.new()
	marker.name = "ScaleMarker"
	marker.position.y = 0.825
	var capsule := CapsuleMesh.new()
	capsule.height = 1.65
	capsule.radius = 0.22
	capsule.radial_segments = 12
	capsule.rings = 4
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("cfa865")
	material.roughness = 0.9
	capsule.material = material
	marker.mesh = capsule
	target.add_child(marker)
	marker.owner = room
	var camera := room.get_node("ReviewCamera") as Camera3D
	camera.projection = Camera3D.PROJECTION_PERSPECTIVE
	camera.keep_aspect = Camera3D.KEEP_WIDTH
	camera.fov = 50.0
	camera.position = Vector3(10.5, 2.2, 3.25)
	camera.basis = Basis.looking_at(Vector3(0, -1.375, -8.0))
	var scene := PackedScene.new()
	var error := scene.pack(room)
	if error == OK:
		error = ResourceSaver.save(scene, "res://scenes/dev/room1_camera_follow_test_r1.tscn")
	print("ROOM1_CAMERA_BUILD: ", error)
	room.free()
	quit(error)
