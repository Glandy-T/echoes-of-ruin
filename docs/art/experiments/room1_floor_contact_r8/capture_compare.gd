extends SceneTree

const OUT := "res://docs/art/experiments/room1_floor_contact_r8/evidence/"
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
	records.append({"file":name+".png", "note":note, "contact_floor":room.floor_contact_enabled, "r8_irradiance":room.surface_lighting_enabled, "base_color":room.base_color_mode, "position":[camera.global_position.x,camera.global_position.y,camera.global_position.z], "fov":camera.fov, "geometry":room.baked_geometry_path, "irradiance":room.irradiance_path})
	return image

func _game(x: float, z: float) -> void:
	room.teleport_player(Vector3(x, 0.0, z))
	camera.fov = 50.0
	room._sync_render_camera()
	room._sync_bloom_camera()

func _look(pos: Vector3, target: Vector3, fov: float = 52.0) -> void:
	camera.global_position = pos
	camera.look_at(target)
	camera.fov = fov
	room._sync_render_camera()
	room._sync_bloom_camera()

func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	room = load("res://scenes/dev/room1_floor_contact_r8.tscn").instantiate()
	get_root().add_child(room)
	await _wait()
	room.position_structure_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	room.set_full_surface_mode(3)
	camera = room.get_node("ReviewCamera") as Camera3D
	var stations := [{"tag":"left_front","x":3.525,"z":-3.4},{"tag":"center_front","x":10.5,"z":-3.4},{"tag":"right_front","x":17.475,"z":-3.4},{"tag":"left_back","x":3.525,"z":-5.75},{"tag":"center_back","x":10.5,"z":-5.75},{"tag":"right_back","x":17.475,"z":-5.75}]
	# A = unchanged r7 floor and GI. This must remain an exact r7 normal baseline.
	room.set_floor_contact(false)
	room.set_surface_lighting(false)
	for station in stations:
		_game(station.x, station.z)
		await _snap("game_%s_A_r7floor_r7gi" % station.tag, "A: old r7 floor + old r7 GI")
	_game(17.475, -4.75)
	var r7_exact := await _snap("game_right_baseline_A_exact", "A: exact comparison position against r7 game_right_before_n")
	var r7_baseline := Image.load_from_file(ProjectSettings.globalize_path("res://docs/art/experiments/room1_surface_lighting_r7/evidence/game_right_before_n.png"))
	assert(not r7_baseline.is_empty())
	assert(r7_exact.get_data() == r7_baseline.get_data())
	# B isolates the authored floor maps without accepting a new bake.
	room.set_floor_contact(true)
	for station in [{"tag":"left","x":3.525},{"tag":"center","x":10.5},{"tag":"right","x":17.475}]:
		_game(station.x, -4.75)
		await _snap("game_%s_B_r8floor_r7gi" % station.tag, "B: r8 floor + old r7 GI; material isolation")
	# C is the default authored result: r8 floor plus its matching bake.
	room.set_surface_lighting(true)
	for station in stations:
		_game(station.x, station.z)
		await _snap("game_%s_C_r8floor_r8gi" % station.tag, "C: r8 floor + r8 GI default")
	_game(17.475, -4.75)
	var c_before := await _snap("game_right_baseline_C", "C: normal reference for toggle round trips")
	room.set_base_color_mode(true)
	await _snap("game_right_n_basecolor", "N: Base Color diagnostic")
	room.set_base_color_mode(false)
	var c_after_n := await _snap("game_right_after_n", "N restored")
	assert(c_before.get_data() == c_after_n.get_data())
	room.set_floor_contact(false)
	await _snap("game_right_f_oldfloor", "F: old r7 floor while r8 GI remains")
	room.set_floor_contact(true)
	var c_after_f := await _snap("game_right_after_f", "F restored")
	assert(c_before.get_data() == c_after_f.get_data())
	room.set_surface_lighting(false)
	await _snap("game_right_i_r7gi", "I: r7 GI while r8 floor remains")
	room.set_surface_lighting(true)
	var c_after_i := await _snap("game_right_after_i", "I restored")
	assert(c_before.get_data() == c_after_i.get_data())
	# Base contact inspection: four ordinary pods and each established leak pod.
	var normal_points := {"P01":Vector3(1.775,0,-1.85),"P05":Vector3(8.775,0,-1.85),"P15":Vector3(8.775,0,-7.65),"P20":Vector3(19.225,0,-7.65)}
	for id in normal_points:
		var point: Vector3 = normal_points[id]
		var inside_offset := Vector3(-2.35,2.25,2.55) if point.x > 17.0 else Vector3(2.35,2.25,2.55)
		_look(point + inside_offset, point + Vector3(0,0.18,0), 52)
		await _snap("pod_contact_%s_C" % id, "normal pod base contact and two floor corners")
	var leak_points := {"P03":Vector3(5.275,0,-1.85),"P06":Vector3(12.225,0,-1.85),"P13":Vector3(5.275,0,-7.65),"P18":Vector3(15.725,0,-7.65)}
	for id in leak_points:
		var point: Vector3 = leak_points[id]
		_look(point + Vector3(2.35,2.25,2.55), point + Vector3(0,0.18,0), 52)
		await _snap("leak_contact_%s_C" % id, "fixed leak pod: residue and grounded base contact")
	# The only elevated diagnostic is Base Color, to reveal map-only borders without lighting changes.
	room.set_base_color_mode(true)
	_look(Vector3(10.5,24,-1), Vector3(10.5,0,-4.75), 53)
	await _snap("floor_basecolor_overview", "Base Color: full floor perimeter and all 20 pod outlines")
	room.set_base_color_mode(false)
	FileAccess.open(OUT+"capture_record.json", FileAccess.WRITE).store_string(JSON.stringify({"scene":"room1_floor_contact_r8.tscn","captures":records,"checks":{"r7_baseline_exact":true,"n_roundtrip_exact":true,"f_roundtrip_exact":true,"i_roundtrip_exact":true,"resolution":[1280,720],"modes":{"A":"r7 floor+r7 GI","B":"r8 floor+r7 GI","C":"r8 floor+r8 GI"}}}))
	print("ROOM1_FLOOR_CONTACT_R8_COMPARE_COMPLETE")
	quit()
