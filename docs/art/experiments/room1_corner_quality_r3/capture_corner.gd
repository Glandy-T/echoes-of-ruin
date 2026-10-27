extends SceneTree
const OUT := "res://docs/art/experiments/room1_corner_quality_r3/evidence/"
func _initialize() -> void:
	call_deferred("capture")
func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var records: Array = []
	for version in ["r2", "r3"]:
		var room: Node = load("res://scenes/dev/room1_surface_sample_r1.tscn").instantiate()
		room.lightmap_bake_override = "res://assets/art/room1_open_hero_uv2_r2" if version == "r2" else "res://assets/art/room1_corner_quality_r3"
		get_root().add_child(room)
		for frame in 15: await process_frame
		room.position_surface_review()
		room.set_process(false)
		room.set_physics_process(false)
		room.info.get_parent().visible = false
		var camera := room.get_node("ReviewCamera") as Camera3D
		var positions := [Vector3(3.525,0,-4.75),Vector3(3.525,0,-3.35)]
		for view in positions.size():
			room.teleport_player(positions[view])
			room._sync_render_camera()
			room._sync_bloom_camera()
			for mode in [0,3]:
				room.set_surface_sample_mode(mode)
				for frame in 15: await process_frame
				await RenderingServer.frame_post_draw
				var name := "%02d_%s_%s" % [view+1,version,"baseline" if mode==0 else "sample"]
				var image := get_root().get_texture().get_image()
				assert(image.save_png(OUT+name+".png") == OK)
				assert(image.get_region(Rect2i(170,35,350,400)).save_png(OUT+name+"_corner.png") == OK)
				records.append({"file":name+".png","size":[image.get_width(),image.get_height()],
					"bake_geometry":room.baked_geometry_path,"irradiance":room.irradiance_path,
					"camera_position":[camera.position.x,camera.position.y,camera.position.z],
					"camera_basis":str(camera.basis),"fov":camera.fov,"sample_mode":mode,
					"corner_crop":[170,35,350,400]})
		room.queue_free()
		for frame in 5: await process_frame
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"  "))
	print("CORNER_COMPARE_COMPLETE")
	quit()
