extends SceneTree
func _initialize() -> void:
	call_deferred("run_checks")
func run_checks() -> void:
	var room = load("res://scenes/dev/room1_hero_scale_review_r1.tscn").instantiate()
	root.add_child(room)
	for i in 20:
		await physics_frame
	assert(is_equal_approx(room.paper_hero.pixel_size * 96.0, 1.4025))
	room.smaller_hero = false
	room.apply_hero_size()
	assert(is_equal_approx(room.paper_hero.pixel_size * 96.0, 1.65))
	room.smaller_hero = true
	room.apply_hero_size()
	for n in range(1, 21):
		if n == 12:
			continue
		var pod = room.get_node("Pods/P%02d" % n)
		for spec in [["pod_v3_shell_end", Vector2i(58, 38), 2], ["pod_v3_lid", Vector2i(69, 199), 1]]:
			var mesh = pod.find_child(spec[0], true, false)
			var texture = mesh.get_active_material(0).get_shader_parameter("color_map")
			var img: Image = texture.get_image()
			var start: Vector2i = spec[1]
			var scale: int = spec[2]
			var ink: Color = img.get_pixel(start.x + scale, start.y)
			var background: Color = img.get_pixel(start.x + 3 * scale, start.y)
			if ink == background:
				push_error("No contrasting ink for P%02d %s: %s; start %s" % [n, spec[0], ink, img.get_pixel(start.x, start.y)])
				quit(1)
				return
			for d in 2:
				var digit: int = n / 10 if d == 0 else n % 10
				var pattern: String = room.DIGITS[digit]
				for y in 5:
					for x in 3:
						var pixel := img.get_pixel(start.x + (d * 4 + x) * scale, start.y + y * scale)
						assert(pixel == (ink if pattern[y * 3 + x] == "1" else background))
	assert(room.standard != null)
	print("PASS: both hero scales; numbered lid and end textures on 19 old pods; P12 retained")
	quit()
