extends SceneTree

const OUT := "res://docs/art/experiments/room1_surface_lighting_r7/evidence/"
const RAW_IRRADIANCE := preload("res://assets/art/room1_surface_lighting_r7/strip_irradiance.exr")
const R4_IRRADIANCE := preload("res://assets/art/room1_wall_finish_r4/strip_irradiance_denoised.exr")
const R7_IRRADIANCE := preload("res://assets/art/room1_surface_lighting_r7/strip_irradiance_denoised.exr")
var room: Node
var camera: Camera3D
var records: Array = []

func _initialize() -> void:
	call_deferred("capture")

func _wait() -> void:
	for _i in 15: await process_frame
	await RenderingServer.frame_post_draw

func _snap(name: String, note: String) -> Image:
	await _wait()
	var image := get_root().get_texture().get_image()
	assert(image.get_width() == 1280 and image.get_height() == 720)
	assert(image.save_png(OUT + name + ".png") == OK)
	records.append({"file":name+".png", "note":note, "r7_irradiance":room.surface_lighting_enabled,
		"base_color":room.base_color_mode, "position":[camera.global_position.x,camera.global_position.y,camera.global_position.z], "fov":camera.fov,
		"geometry":room.baked_geometry_path, "irradiance":room.irradiance_path})
	return image

func _game(x: float, z: float) -> void:
	room.teleport_player(Vector3(x,0.0,z))
	camera.fov = 50.0
	room._sync_render_camera()
	room._sync_bloom_camera()

func _set_raw(enabled: bool) -> void:
	for material: ShaderMaterial in room.baked_receivers:
		material.set_shader_parameter("strip_irradiance", RAW_IRRADIANCE if enabled else R7_IRRADIANCE)
	room.irradiance_path = RAW_IRRADIANCE.resource_path if enabled else R7_IRRADIANCE.resource_path

func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	room=load("res://scenes/dev/room1_surface_lighting_r7.tscn").instantiate()
	get_root().add_child(room)
	await _wait()
	room.position_structure_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible=false
	camera=room.get_node("ReviewCamera") as Camera3D
	room.set_full_surface_mode(3)
	var stations=[{"tag":"left_front","x":3.525,"z":-3.4},{"tag":"center_front","x":10.5,"z":-3.4},{"tag":"right_front","x":17.475,"z":-3.4},{"tag":"left_back","x":3.525,"z":-5.75},{"tag":"center_back","x":10.5,"z":-5.75},{"tag":"right_back","x":17.475,"z":-5.75}]
	# Identical cameras: old r4 irradiance versus the r7 bake.
	for r7 in [false,true]:
		room.set_surface_lighting(r7)
		for station in stations:
			_game(station.x,station.z)
			await _snap("game_%s_%s" % [station.tag,"r7" if r7 else "r4"],"same gameplay camera")
	# The albedo diagnosis must not depend on the irradiance selected by I.
	_game(17.475,-4.75)
	room.set_surface_lighting(true)
	room.set_base_color_mode(true)
	var r7_base:=await _snap("base_color_r7","r7 GI selected; Base Color diagnostic")
	room.set_base_color_mode(false)
	room.set_surface_lighting(false)
	room.set_base_color_mode(true)
	var r4_base:=await _snap("base_color_r4","r4 GI selected; Base Color diagnostic")
	assert(r7_base.get_data()==r4_base.get_data())
	room.set_base_color_mode(false)
	room.set_surface_lighting(true)
	var before_n:=await _snap("game_right_before_n","r7 normal, before N")
	room.set_base_color_mode(true)
	await _snap("game_right_n","r7 Base Color")
	room.set_base_color_mode(false)
	var after_n:=await _snap("game_right_after_n","r7 normal, N restored")
	assert(before_n.get_data()==after_n.get_data())
	room.set_surface_lighting(false)
	await _snap("game_right_r4_roundtrip_mid","r4 intermediate, I toggle")
	room.set_surface_lighting(true)
	var after_i:=await _snap("game_right_after_i","r7 normal, I restored")
	assert(before_n.get_data()==after_i.get_data())
	# Raw versus denoised is a technical check only; no exposure or color adjustment.
	_game(3.525,-4.75)
	_set_raw(true)
	await _snap("raw_left_corner","raw 1024-sample EXR")
	_set_raw(false)
	await _snap("denoised_left_corner","denoised r7 EXR")
	var leak_points := {"P03":Vector3(5.275,0,-1.85),"P06":Vector3(12.225,0,-1.85),"P13":Vector3(5.275,0,-7.65),"P18":Vector3(15.725,0,-7.65)}
	for pod_name in leak_points:
		var point: Vector3 = leak_points[pod_name]
		camera.global_position=point+Vector3(2.35,2.25,2.55)
		camera.look_at(point+Vector3(0,0.18,0))
		camera.fov=52
		room._sync_render_camera();room._sync_bloom_camera()
		await _snap("leak_%s_r7" % pod_name,"r7 GI: pod base and fixed old leak residue")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify({"scene":"room1_surface_lighting_r7.tscn","captures":records,"checks":{"base_color_r4_r7_exact":true,"n_roundtrip_exact":true,"i_roundtrip_exact":true,"resolution":[1280,720]}}))
	print("ROOM1_SURFACE_LIGHTING_R7_COMPARE_COMPLETE")
	quit()
