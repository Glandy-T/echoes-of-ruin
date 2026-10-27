extends SceneTree
const OUT := "res://docs/art/experiments/room1_left_wall_uv2_fix_r2/evidence/"

func _initialize() -> void:
	call_deferred("render_fix")

func render_fix() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var records: Array = []
	for legacy in [true, false]:
		var room: Node = load("res://scenes/dev/room1_surface_sample_r1.tscn").instantiate()
		room.legacy_lightmap_for_review = legacy
		get_root().add_child(room)
		for frame in 15:
			await process_frame
		room.position_surface_review()
		room.set_process(false)
		room.set_physics_process(false)
		room.info.get_parent().visible = false
		var camera := room.get_node("ReviewCamera") as Camera3D
		var prefix := "legacy" if legacy else "fixed"
		for mode in [0,3]:
			room.set_surface_sample_mode(mode)
			for frame in 15:
				await process_frame
			await RenderingServer.frame_post_draw
			var name := prefix + ("_baseline.png" if mode == 0 else "_sample.png")
			var image := get_root().get_texture().get_image()
			image.save_png(OUT+name)
			records.append({"image":name,"size":[image.get_width(),image.get_height()],
				"bake_geometry":room.baked_geometry_path,"irradiance":room.irradiance_path,
				"camera_position":[camera.position.x,camera.position.y,camera.position.z],
				"camera_basis":str(camera.basis),"fov":camera.fov,"sample_mode":mode})
		room.queue_free()
		for frame in 5:
			await process_frame
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify({
		"scope":"Same-camera review of real UV2 repack and rebake; not a lighting mask or texture repaint.",
		"captures":records},"  "))
	print("UV2_FIX_REVIEW_CAPTURE_COMPLETE")
	quit()
