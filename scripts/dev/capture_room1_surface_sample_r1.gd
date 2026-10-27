extends SceneTree

const OUT := "res://docs/art/experiments/room1_surface_sample_r1/evidence/"

func _initialize() -> void:
	call_deferred("render_review")

func render_review() -> void:
	var room := load("res://scenes/dev/room1_surface_sample_r1.tscn").instantiate() as Node3D
	if not room.has_method("position_surface_review"):
		push_error("Surface review script did not load; stopping render.")
		quit(1)
		return
	get_root().add_child(room)
	for frame in 10:
		await process_frame
	room.position_surface_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	DirAccess.make_dir_recursive_absolute(OUT)
	var camera := room.get_node("ReviewCamera") as Camera3D
	var record := {"source_scene": "room1_pod_exit_animation_r3.tscn",
		"review_scene": "room1_surface_sample_r1.tscn", "bake_geometry":room.baked_geometry_path,
		"irradiance":room.irradiance_path, "views": []}
	var positions := [Vector3(3.525, 0, -4.75), Vector3(3.525, 0, -3.35)]
	var modes := ["baseline", "wall_only", "floor_only", "wall_floor"]
	for view in positions.size():
		room.teleport_player(positions[view])
		room._sync_render_camera()
		room._sync_bloom_camera()
		var shots: Array = []
		for mode in 4:
			room.set_surface_sample_mode(mode)
			for frame in 12:
				await process_frame
			await RenderingServer.frame_post_draw
			var filename := "%02d_%s.png" % [view + 1, modes[mode]]
			var image := get_root().get_texture().get_image()
			var error := image.save_png(OUT + filename)
			shots.append({"file": filename, "size": [image.get_width(), image.get_height()], "save_error": error})
		record["views"].append({"player_position": [positions[view].x,positions[view].y,positions[view].z],
			"camera_position": [camera.position.x,camera.position.y,camera.position.z],
			"camera_basis": str(camera.basis), "fov": camera.fov, "shots":shots})
	record["selected_materials"] = {}
	for key in room.surface_materials:
		record["selected_materials"][key] = room.surface_materials[key].size()
	record["scope"] = "Review renders only. UV2 baked lighting and inherited capsule shadows retained; no gameplay tests or art approval."
	FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify(record, "  "))
	print("SURFACE_REVIEW_RENDER_COMPLETE")
	quit()
