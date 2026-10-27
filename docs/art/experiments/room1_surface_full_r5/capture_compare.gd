extends SceneTree

const OUT := "res://docs/art/experiments/room1_surface_full_r5/evidence/"
const BASELINE := "res://docs/art/experiments/room1_wall_age_r4/evidence/game_r4_lit.png"
const LEAK_PODS := {"P03": Vector3(5.275, 0.0, -1.85), "P06": Vector3(12.225, 0.0, -1.85), "P13": Vector3(5.275, 0.0, -7.65), "P18": Vector3(15.725, 0.0, -7.65)}
var room: Node
var camera: Camera3D
var records: Array = []

func _initialize() -> void: call_deferred("capture")
func _wait() -> void:
	for _i in 15: await process_frame
	await RenderingServer.frame_post_draw
func _snap(name: String, note: String) -> Image:
	await _wait()
	var image := get_root().get_texture().get_image()
	assert(image.get_width() == 1280 and image.get_height() == 720)
	assert(image.save_png(OUT + name + ".png") == OK)
	records.append({"file":name+".png", "note":note, "mode":room.full_mode, "base_color":room.base_color_mode, "camera":[camera.global_position.x,camera.global_position.y,camera.global_position.z], "fov":camera.fov, "geometry":room.baked_geometry_path, "irradiance":room.irradiance_path, "hdr":"r4 continuous strip UV2 irradiance; unchanged"})
	return image
func _game(x: float) -> void:
	room.teleport_player(Vector3(x, 0.0, -4.75)); camera.fov=50.0; room._sync_render_camera(); room._sync_bloom_camera()
func _assert_baseline(image: Image) -> void:
	var baseline := Image.load_from_file(BASELINE)
	assert(baseline != null and not baseline.is_empty() and baseline.get_data() == image.get_data())
func _overview() -> void:
	camera.global_position=Vector3(10.5,15.0,-1.0); camera.look_at(Vector3(10.5,0.0,-4.75)); camera.fov=53.0; room._sync_render_camera(); room._sync_bloom_camera()
func _leak_view(point: Vector3) -> void:
	camera.global_position=point+Vector3(2.35,2.25,2.55); camera.look_at(point+Vector3(0.0,0.18,0.0)); camera.fov=52.0; room._sync_render_camera(); room._sync_bloom_camera()
func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	room=load("res://scenes/dev/room1_surface_full_r5.tscn").instantiate(); get_root().add_child(room); await _wait()
	room.position_structure_review(); room.set_process(false); room.set_physics_process(false); room.info.get_parent().visible=false; camera=room.get_node("ReviewCamera") as Camera3D
	# All four modes in the same left/centre/right gameplay coverage.
	for mode in 4:
		room.set_base_color_mode(false); room.set_full_surface_mode(mode)
		for station in [{"tag":"left","x":3.525},{"tag":"center","x":10.5},{"tag":"right","x":17.475}]:
			_game(station.x); var image := await _snap("game_%s_m%d" % [station.tag,mode], "same gameplay view; M=%d" % mode)
			if mode==0 and station.tag=="left": _assert_baseline(image)
	# Pure painted-color overview is kept separate from the lit comparisons.
	room.set_full_surface_mode(3); room.set_base_color_mode(true); _overview(); await _snap("overview_m3_base_color", "whole room base-color diagnostic")
	room.set_base_color_mode(false)
	for pod_name in LEAK_PODS:
		_leak_view(LEAK_PODS[pod_name]); await _snap("leak_%s_m3_lit" % pod_name, "lit leak inspection: pod base and surrounding floor")
	_game(3.525); room.set_full_surface_mode(0); room.set_base_color_mode(true); await _snap("game_left_m0_base_color", "N diagnostic before restoration")
	room.set_base_color_mode(false); var roundtrip := await _snap("game_left_m0_after_n_roundtrip", "N restored; exact r4 baseline required"); _assert_baseline(roundtrip)
	var aabb := []
	for pod_name in LEAK_PODS:
		var pod := room.get_node("Pods/"+pod_name) as Node3D
		var bounds := AABB()
		var first := true
		for mesh: MeshInstance3D in pod.find_children("*", "MeshInstance3D", true, false):
			var local_bounds := mesh.get_aabb()
			for corner in 8:
				var local_corner := local_bounds.get_endpoint(corner)
				var world_corner := mesh.global_transform * local_corner
				if first: bounds = AABB(world_corner, Vector3.ZERO); first = false
				else: bounds = bounds.expand(world_corner)
		aabb.append({"pod":pod_name,"origin":[pod.global_position.x,pod.global_position.y,pod.global_position.z],"world_aabb":{"position":[bounds.position.x,bounds.position.y,bounds.position.z],"size":[bounds.size.x,bounds.size.y,bounds.size.z]}})
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify({"scene":"room1_surface_full_r5.tscn","default_mode":3,"wall_maps":{"left":"res://assets/art/room1_surface_full_r5/wall_left.png","right":"res://assets/art/room1_surface_full_r5/wall_right.png","front":"res://assets/art/room1_surface_full_r5/wall_front.png","rear":"res://assets/art/room1_surface_full_r5/wall_rear.png"},"floor_maps":{"aged":"res://assets/art/room1_surface_full_r5/floor_aged.png","leaks":"res://assets/art/room1_surface_full_r5/floor_with_leaks.png"},"mapping":{"side_u":"(-world_z-0.2)/9.1","front_rear_u":"(world_x-0.2)/20.6","wall_v":"1-world_y/3.4","floor_uv":"((world_x-0.2)/20.6,(world_z+9.3)/9.1)"},"leak_candidates":aabb,"captures":records}))
	print("ROOM1_SURFACE_FULL_R5_COMPARE_COMPLETE"); quit()
