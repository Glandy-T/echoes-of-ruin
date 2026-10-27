extends SceneTree
func _initialize() -> void:
	call_deferred("capture")
func capture() -> void:
	var room: Node = load("res://scenes/dev/room1_surface_sample_r1.tscn").instantiate()
	get_root().add_child(room)
	for frame in 15: await process_frame
	room.position_surface_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	var original: Dictionary = {}
	for material in room.baked_receivers:
		original[material] = material.shader.code
	for variant in ["raw"]:
		var expression: String = {"raw":"UV2","flip_v":"vec2(UV2.x, 1.0-UV2.y)","flip_u":"vec2(1.0-UV2.x, UV2.y)","flip_uv":"vec2(1.0)-UV2"}[variant]
		for material in room.baked_receivers:
			var shader := Shader.new()
			shader.code = original[material].replace("texture(strip_irradiance, UV2)","texture(strip_irradiance, "+expression+")")
			material.shader = shader
			material.set_shader_parameter("strip_irradiance", load("res://assets/art/room1_open_hero_uv2_r2/strip_irradiance.exr"))
		for frame in 15: await process_frame
		await RenderingServer.frame_post_draw
		get_root().get_texture().get_image().save_png("res://docs/art/experiments/room1_left_wall_uv2_fix_r2/probe_"+variant+".png")
	quit()

