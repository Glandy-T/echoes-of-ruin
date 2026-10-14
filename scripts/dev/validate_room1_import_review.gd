extends SceneTree

const EVIDENCE := "res://docs/art/experiments/room1_godot_review_r1/"
var report := {"engine": Engine.get_version_info().string, "renderer": "gl_compatibility", "models": [], "checks": {}, "screenshots": []}

func _initialize() -> void:
	call_deferred("_review")

func _review() -> void:
	DirAccess.make_dir_recursive_absolute(EVIDENCE)
	for file: String in ["room1_shell_full_r1.glb", "room1_layout_review_r1.glb", "pod_closed_v3.glb", "pod_open_v3.glb"]:
		var resource := load("res://assets/art/room1_revision_20261013/" + file) as PackedScene
		assert(resource != null, "GLB failed to load: " + file)
		var instance := resource.instantiate()
		var summary := {"file": file, "meshes": 0, "textured_surfaces": 0, "filters": [], "uv0_surfaces": 0}
		_inspect(instance, summary)
		report.models.append(summary)
		assert(summary.textured_surfaces > 0)
		assert(summary.filters == [0], "Non-nearest texture in " + file)
		instance.free()
	var room := (load("res://scenes/dev/room1_import_review_r1.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	await process_frame
	assert(room.get_node("Pods").get_child_count() == 20)
	report.checks["pod_count"] = 20
	var entries: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/room1_revision_20261013/pod_placement_godot.json"))
	for entry: Dictionary in entries.placements:
		var xyz: Array = entry.position_godot_m
		var pod := room.get_node("Pods/" + entry.id) as Node3D
		assert(pod.position.is_equal_approx(Vector3(xyz[0], xyz[1], xyz[2])))
		assert(pod.basis.is_equal_approx(Basis(Vector3.UP, float(entry.rotation_y_radians))))
	report.checks["placements_match_manifest"] = true
	var hidden_names: Array[String] = []
	for node_name: String in room.CUTAWAY_NAMES:
		var object := room.get_node("Shell").find_child(node_name, true, false) as Node3D
		assert(object != null and not object.visible)
		hidden_names.append(node_name)
	report.checks["cutaway_hidden"] = hidden_names
	await _capture("01_overview.png")
	room._set_view(2)
	await _capture("02_pod_closed.png")
	room._toggle_pose()
	assert(room.get_node("Pods").get_child_count() == 20)
	assert(room.open_pose)
	await _capture("03_pod_open_static.png")
	room._toggle_pose()
	room._set_view(3)
	await _capture("04_door_wall.png")
	room.get_node("ReviewLights").visible = false
	room._update_status()
	await _capture("05_lights_off.png")
	room.get_node("ReviewLights").visible = true
	room.cutaway = false
	room._apply_cutaway()
	for node_name: String in room.CUTAWAY_NAMES:
		assert(room.get_node("Shell").find_child(node_name, true, false).visible)
	report.checks["full_shell_toggle"] = true
	report.checks["static_pose_toggle_keeps_20_pods"] = true
	report["scope"] = "Godot import, placement, sampling and rendered review. No gameplay, collision or art approval. Wall/floor r1 rejected as too clean on 2026-10-14."
	var output := FileAccess.open(EVIDENCE + "validation.json", FileAccess.WRITE)
	output.store_string(JSON.stringify(report, "\t"))
	output.close()
	print("ROOM1_REVIEW_PASS: ", JSON.stringify(report.checks))
	room.queue_free()
	quit()

func _inspect(node: Node, summary: Dictionary) -> void:
	if node is MeshInstance3D and node.mesh:
		summary.meshes += 1
		for surface in node.mesh.get_surface_count():
			var material := node.mesh.surface_get_material(surface) as BaseMaterial3D
			if material and material.albedo_texture:
				summary.textured_surfaces += 1
				if not summary.filters.has(material.texture_filter):
					summary.filters.append(material.texture_filter)
			var arrays: Array = node.mesh.surface_get_arrays(surface)
			if arrays[Mesh.ARRAY_TEX_UV] != null and arrays[Mesh.ARRAY_TEX_UV].size() > 0:
				summary.uv0_surfaces += 1
	for child in node.get_children():
		_inspect(child, summary)

func _capture(filename: String) -> void:
	for frame in 12:
		await process_frame
	if DisplayServer.get_name() == "headless":
		return
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	assert(image != null and not image.is_empty())
	assert(image.save_png(EVIDENCE + filename) == OK)
	report.screenshots.append(filename)
