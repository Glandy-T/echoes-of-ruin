extends SceneTree

const OUT := "res://docs/art/experiments/protagonist_idle_45_breath_r2/"
const DURATIONS := [6, 5, 5, 3, 5, 4] # Tenths of a second at 10 fps.
const DIRECTIONS := ["45"]

func _initialize() -> void:
	capture.call_deferred()

func build_frames() -> SpriteFrames:
	var bank := SpriteFrames.new()
	bank.remove_animation(&"default")
	for direction in DIRECTIONS:
		var anim := StringName("breath_" + str(direction))
		bank.add_animation(anim)
		bank.set_animation_loop(anim, true)
		bank.set_animation_speed(anim, 10.0)
		for i in DURATIONS.size():
			var image := Image.load_from_file(OUT + "%s/%02d.png" % [direction, i + 1])
			if image == null or image.get_size() != Vector2i(128, 128):
				return null
			var texture := PortableCompressedTexture2D.new()
			texture.keep_compressed_buffer = true
			texture.create_from_image(image, PortableCompressedTexture2D.COMPRESSION_MODE_LOSSLESS)
			bank.add_frame(anim, texture, DURATIONS[i])
	var path := OUT + "breathing.res"
	if ResourceSaver.save(bank, path) != OK:
		return null
	return ResourceLoader.load(path, "SpriteFrames", ResourceLoader.CACHE_MODE_IGNORE) as SpriteFrames

func capture() -> void:
	var bank := build_frames()
	if bank == null:
		printerr("Could not build or reload SpriteFrames")
		quit(2)
		return
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
	var height: float = room.paper_hero.pixel_size * 96.0
	var temp_dir := OS.get_temp_dir().path_join("eor_idle45_breath_r2_review")
	DirAccess.make_dir_recursive_absolute(temp_dir)
	for direction in DIRECTIONS:
		var anim := StringName("breath_" + str(direction))
		# Pin the scale and floor pivot to frame 01 throughout the cycle.
		var bounds := bank.get_frame_texture(anim, 0).get_image().get_used_rect()
		for i in DURATIONS.size():
			var texture := bank.get_frame_texture(anim, i)
			var original := Image.load_from_file(OUT + "%s/%02d.png" % [direction, i + 1])
			var decoded := texture.get_image()
			decoded.convert(Image.FORMAT_RGBA8)
			original.convert(Image.FORMAT_RGBA8)
			if decoded.get_data() != original.get_data() or bank.get_frame_duration(anim, i) != DURATIONS[i]:
				printerr("SpriteFrames round-trip mismatch ", direction, " ", i + 1)
				quit(3)
				return
			for sprite in [room.paper_hero, room.bloom_paper_hero]:
				sprite.texture = texture
				sprite.hframes = 1
				sprite.vframes = 1
				sprite.frame = 0
				sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
				sprite.pixel_size = height / bounds.size.y
				sprite.position.y = (bounds.end.y - 64.0) * sprite.pixel_size
			room._sync_paper_hero()
			room._sync_paper_lighting()
			for _i in 10:
				await process_frame
			await RenderingServer.frame_post_draw
			var shot := root.get_texture().get_image()
			var name := "%s_%02d.png" % [direction, i+1]
			if shot.save_png(temp_dir.path_join(name)) != OK:
				quit(4)
				return
			if i == 3:
				if shot.save_png(OUT + "%s/room_1.png" % direction) != OK:
					quit(4)
					return
	print("Captured 6 Room 1 exposures")
	quit()
