extends SceneTree
const OUT := "res://docs/art/experiments/room1_left_wall_dark_patch_diagnosis_v1/"

func _initialize() -> void:
	call_deferred("capture_channels")

func capture_channels() -> void:
	var room: Node = load("res://scenes/dev/room1_surface_sample_r1.tscn").instantiate()
	room.legacy_lightmap_for_review = true
	get_root().add_child(room)
	for frame in 10:
		await process_frame
	room.position_surface_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	room.set_surface_sample_mode(0)
	await capture("01_original.png")
	room.actor_shadow_on = false
	room._sync_actor_shadow()
	await capture("02_no_actor_shadow.png")
	var left := room.get_node("Shell").find_child("Wall_left", true, false) as MeshInstance3D
	var records: Array = []
	var materials: Array[ShaderMaterial] = []
	var colors: Array = []
	var lights: Array = []
	for surface in left.mesh.get_surface_count():
		var material := left.get_active_material(surface) as ShaderMaterial
		var color := material.get_shader_parameter("color_map") as Texture2D
		if color.get_width() <= 32:
			continue
		materials.append(material)
		colors.append(color)
		lights.append(material.get_shader_parameter("strip_irradiance"))
		records.append({"surface":surface,"color_path":color.resource_path,
			"light_path":(lights[-1] as Texture2D).resource_path})
		material.set_shader_parameter("color_map", room._solid_texture(Color("#D3D6C9")))
	await capture("03_uniform_wall_albedo.png")
	for index in materials.size():
		materials[index].set_shader_parameter("color_map", colors[index])
		materials[index].set_shader_parameter("strip_irradiance", room._solid_texture(Color(0.15,0.15,0.15)))
	await capture("04_uniform_wall_irradiance.png")
	var raw := load("res://assets/art/room1_open_hero_bake_r1/strip_irradiance.exr") as Texture2D
	for index in materials.size():
		materials[index].set_shader_parameter("strip_irradiance", raw)
	await capture("05_raw_before_denoise.png")
	# Unfold just the lighting on each inner wall; this is a diagnostic image,
	# not a proposed wall texture or altered game exposure.
	for wall_name in ["Wall_left", "Wall_right"]:
		var mesh := room.get_node("Shell").find_child(wall_name,true,false) as MeshInstance3D
		for surface in mesh.mesh.get_surface_count():
			var mat := mesh.get_active_material(surface) as ShaderMaterial
			var color := mat.get_shader_parameter("color_map") as Texture2D
			if color.get_width()<=32:
				continue
			var arrays := mesh.mesh.surface_get_arrays(surface)
			var uv: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
			var uv2: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV2]
			var base := Transform2D(uv[1]-uv[0],uv[2]-uv[0],uv[0]).affine_inverse()
			var target := Transform2D(uv2[1]-uv2[0],uv2[2]-uv2[0],uv2[0])
			for mode in ["raw","denoised"]:
				var map := raw if mode=="raw" else lights[0] as Texture2D
				var image := map.get_image()
				var unwrapped := Image.create(728,272,false,Image.FORMAT_RGB8)
				for y in 272:
					for x in 728:
						var p := target * (base * Vector2((x+.5)/728.0,(y+.5)/272.0))
						var value := image.get_pixel(clampi(int(p.x*image.get_width()),0,image.get_width()-1),clampi(int(p.y*image.get_height()),0,image.get_height()-1))
						unwrapped.set_pixel(x,y,Color(value.r*.5,value.g*.5,value.b*.5).linear_to_srgb())
				unwrapped.save_png(OUT+wall_name+"_"+mode+"_lighting.png")
	FileAccess.open(OUT+"channel_record.json", FileAccess.WRITE).store_string(JSON.stringify(records,"  "))
	print("LEFT_WALL_CHANNEL_CAPTURE_COMPLETE")
	quit()

func capture(filename: String) -> void:
	for frame in 12:
		await process_frame
	await RenderingServer.frame_post_draw
	get_root().get_texture().get_image().save_png(OUT+filename)
