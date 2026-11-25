extends SceneTree

const OUT := "res://docs/art/experiments/protagonist_walk_side_r2/"

func _initialize() -> void:
	capture.call_deferred()

func capture() -> void:
	var report: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OUT + "gait.json"))
	var frames: Array = report["samples"]
	var period: float = report["period_s"]
	var room = load("res://scenes/dev/room1_door_light_recess_b1.tscn").instantiate()
	root.add_child(room)
	for _i in 20:
		await process_frame
	room.set_pixel_mode(0)
	room.finish_exit()
	room.review_ui.close_dialogue()
	room.teleport_player(Vector3(10.5, 0.05, -4.75))
	var cam: Camera3D = room.get_node("ReviewCamera")
	cam.fov = 50.0
	room._sync_render_camera()
	room._sync_bloom_camera()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().hide()
	var screen_right := cam.global_transform.basis.x
	screen_right.y = 0
	screen_right = screen_right.normalized()
	var center: Vector3 = room.player.global_position
	var textures: Array[ImageTexture] = []
	for i in frames.size():
		var img := Image.load_from_file(OUT + "cycle_%02d.png" % (i + 1))
		if img == null or img.get_size() != Vector2i(128, 128):
			quit(2)
			return
		textures.append(ImageTexture.create_from_image(img))
	var temp_dir := OS.get_environment("TEMP").path_join("echoes_room_walk_r2")
	DirAccess.make_dir_recursive_absolute(temp_dir)
	# Fixed camera, 2 m/s to screen-left. Four character steps over two loops.
	for t in 32:
		var seconds := t * period / 16.0
		room.player.global_position = center + screen_right * (2.0 * (period - seconds))
		for spr in [room.paper_hero, room.bloom_paper_hero]:
			spr.texture = textures[(t / 2) % frames.size()]
			spr.hframes = 1
			spr.vframes = 1
			spr.frame = 0
			spr.flip_h = false
			spr.pixel_size = 1.65 / 125.0
			spr.position.y = (127.0 - 64.0) * spr.pixel_size
		room._sync_actor_shadow()
		room._sync_paper_hero()
		room._sync_paper_lighting()
		room._sync_door_glow()
		for _i in 3:
			await process_frame
		await RenderingServer.frame_post_draw
		var err := root.get_texture().get_image().save_png(temp_dir.path_join("room_%02d.png" % t))
		if err != OK:
			quit(err)
			return
	quit()
