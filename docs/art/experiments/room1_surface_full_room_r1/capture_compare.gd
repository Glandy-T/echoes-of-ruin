extends SceneTree
const OUT := "res://docs/art/experiments/room1_surface_full_room_r1/evidence/"
func _initialize() -> void:
	call_deferred("capture")
func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var room: Node = load("res://scenes/dev/room1_surface_full_room_r1.tscn").instantiate()
	get_root().add_child(room)
	for frame in 15: await process_frame
	room.position_material_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	var camera := room.get_node("ReviewCamera") as Camera3D
	var records: Array = []
	var bindings: Dictionary = {}
	for name in room.full_surface_materials:
		var values: Array = []
		for material in room.full_surface_materials[name]:
			values.append({"kind":material.get_shader_parameter("full_surface_kind"),
				"strength":material.get_shader_parameter("material_strength"),
				"continuous_diffuser":material.get_shader_parameter("uniform_strip_emission"),
				"diffuser_scale":material.get_shader_parameter("diffuser_radiance_scale"),
				"lightmap":(material.get_shader_parameter("strip_irradiance") as Texture2D).resource_path})
		bindings[name] = values
	for view in 3:
		room.teleport_player(Vector3([3.525,10.5,17.475][view],0,-4.75))
		room._sync_render_camera()
		room._sync_bloom_camera()
		for mode in 4:
			room.set_full_surface_mode(mode)
			for frame in 15: await process_frame
			await RenderingServer.frame_post_draw
			var name := "%02d_%s.png" % [view+1,["baseline","wall","floor","both"][mode]]
			var image := get_root().get_texture().get_image()
			assert(image.save_png(OUT+name)==OK)
			records.append({"file":name,"mode":mode,"size":[image.get_width(),image.get_height()],
				"camera_position":[camera.position.x,camera.position.y,camera.position.z],
				"camera_basis":str(camera.basis),"fov":camera.fov})
	# Stronger material finish for comparison; not the default setting.
	room.set_full_surface_mode(3)
	for materials in room.full_surface_materials.values():
		for material in materials:
			material.set_shader_parameter("material_strength",1.0)
	room.teleport_player(Vector3(3.525,0,-4.75))
	room._sync_render_camera()
	room._sync_bloom_camera()
	for frame in 15: await process_frame
	await RenderingServer.frame_post_draw
	get_root().get_texture().get_image().save_png(OUT+"04_stronger_variation.png")
	var scope := {}
	for name in room.full_surface_materials:
		scope[name] = room.full_surface_materials[name].size()
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify({
		"scene":"room1_surface_full_room_r1.tscn","geometry":room.baked_geometry_path,
		"irradiance":room.irradiance_path,"materials":scope,
		"initial_bindings":bindings,
		"strength":{"wall":room.wall_material_strength,"floor":room.floor_material_strength},
		"scope":"Full-room albedo candidate only; existing r4 UV2/lightmap retained, new albedo bounce not rebaked.",
		"captures":records},"  "))
	print("FULL_ROOM_MATERIAL_COMPARE_COMPLETE")
	quit()
