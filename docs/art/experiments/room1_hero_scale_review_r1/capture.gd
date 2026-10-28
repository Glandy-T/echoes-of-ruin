extends SceneTree

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	var room = load("res://scenes/dev/room1_hero_scale_review_r1.tscn").instantiate()
	root.add_child(room)
	for i in 60:
		await process_frame
	room.info.get_parent().visible = false
	room.review_ui.hide_interaction_name(room.interaction_area)
	for smaller in [false, true]:
		room.smaller_hero = smaller
		room.apply_hero_size()
		for i in 12:
			await process_frame
		await RenderingServer.frame_post_draw
		var filename := "candidate" if smaller else "original"
		var path := "res://docs/art/experiments/room1_hero_scale_review_r1/evidence/" + filename + ".png"
		if root.get_texture().get_image().save_png(path) != OK:
			push_error("Could not save " + path)
			quit(1)
			return
	room.set_physics_process(false)
	room.set_process(false)
	room.player.visible = false
	var camera := room.get_node("ReviewCamera") as Camera3D
	camera.global_position = Vector3(5.275, 1.8, -4.7)
	camera.look_at(Vector3(5.275, 0.5, -1.85), Vector3.UP)
	room._sync_render_camera()
	room._sync_bloom_camera()
	for i in 20:
		await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://docs/art/experiments/room1_hero_scale_review_r1/evidence/front_row_check.png")
	print("Saved original and candidate scale screenshots")
	quit()
