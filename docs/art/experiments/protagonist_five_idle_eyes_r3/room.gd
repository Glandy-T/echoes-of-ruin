extends SceneTree

# Capture review frames only. This script does not save the selected sprite into
# the Room 1 scene, and therefore cannot replace the in-game placeholder.
const OUT := "res://docs/art/experiments/protagonist_five_idle_eyes_r3/"
const B := "res://docs/art/experiments/protagonist_front_c_raw_v2/B_original.png"
const KEYS := ["45","90"]

func _initialize() -> void:
	capture.call_deferred()

func capture() -> void:
	var room := (load("res://scenes/dev/room1_door_light_recess_b1.tscn") as PackedScene).instantiate()
	root.add_child(room)
	for _i in 20:
		await process_frame
	room.set_pixel_mode(0)
	room.finish_exit()
	room.review_ui.close_dialogue()
	room.teleport_player(Vector3(10.5, 0.05, -4.75))
	room.get_node("ReviewCamera").fov = 50.0
	room._sync_render_camera()
	room._sync_bloom_camera()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().hide()

	# The existing paper hero's world height is the comparison baseline.
	var world_height: float = room.paper_hero.pixel_size * 96.0
	for key in KEYS:
		var path: String = B if key == "B" else OUT + "final_" + key + ".png"
		var image := Image.load_from_file(path)
		if image == null or image.get_size() != Vector2i(128, 128):
			printerr("Expected a 128x128 sprite: ", path)
			quit(2)
			return
		var bounds := image.get_used_rect()
		if bounds.size.y <= 0:
			printerr("Sprite has no visible pixels: ", path)
			quit(3)
			return
		var texture := ImageTexture.create_from_image(image)
		for sprite in [room.paper_hero, room.bloom_paper_hero]:
			sprite.texture = texture
			sprite.hframes = 1
			sprite.vframes = 1
			sprite.frame = 0
			sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
			sprite.pixel_size = world_height / bounds.size.y
			# Keeps the lowest visible pixel at the same physical floor height.
			sprite.position.y = (bounds.end.y - image.get_height() * 0.5) * sprite.pixel_size
		room._sync_paper_hero()
		room._sync_paper_lighting()
		for _i in 10:
			await process_frame
		await RenderingServer.frame_post_draw
		var err := root.get_texture().get_image().save_png(OUT + "room_" + key + ".png")
		if err != OK:
			quit(err)
			return
	quit()


