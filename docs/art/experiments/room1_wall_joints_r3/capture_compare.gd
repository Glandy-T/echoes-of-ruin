extends SceneTree

const OUT := "res://docs/art/experiments/room1_wall_joints_r3/evidence/"
const R2_BASELINE := "res://docs/art/experiments/room1_surface_structure_r2/evidence/game_03_both.png"
const SAMPLE := {"wall": {"plane_x": 0.2, "z": [-6.4, -3.2], "height": [0.0, 3.4]}}

var room: Node
var camera: Camera3D
var records: Array = []

func _initialize() -> void:
	call_deferred("capture")

func _capture(name: String, description: String) -> Image:
	for _frame in 15:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	assert(image.save_png(OUT + name + ".png") == OK)
	records.append({
		"file": name + ".png",
		"description": description,
		"size": [image.get_width(), image.get_height()],
		"camera_position": [camera.global_position.x, camera.global_position.y, camera.global_position.z],
		"camera_basis": str(camera.global_transform.basis),
		"fov": camera.fov,
		"structure_mode": room.structure_mode,
		"joint_variant": room.joint_variant,
		"joint_label": "r3_wide_joints" if room.joint_variant == 1 else "r2_continuous",
		"base_color_preview": room.base_color_mode,
	})
	return image

func _set_game_view() -> void:
	room.teleport_player(Vector3(3.525, 0.0, -4.75))
	# The technical close-up uses 60 degrees; gameplay comparisons must restore
	# r2's recorded 50-degree game FOV before every return to this camera.
	camera.fov = 50.0
	room._sync_render_camera()
	room._sync_bloom_camera()

func _set_technical_view() -> void:
	# Capture-only close view, showing one complete 3.2 m left-wall span.
	camera.global_position = Vector3(5.75, 2.65, -1.35)
	camera.look_at(Vector3(0.2, 1.55, -4.8), Vector3.UP)
	camera.fov = 60.0
	room._sync_render_camera()
	room._sync_bloom_camera()

func _assert_r2_roundtrip(image: Image) -> void:
	var baseline := Image.load_from_file(R2_BASELINE)
	assert(baseline != null and not baseline.is_empty())
	assert(baseline.get_size() == image.get_size())
	assert(baseline.get_format() == image.get_format())
	assert(baseline.get_data() == image.get_data())

func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	room = load("res://scenes/dev/room1_wall_joints_r3.tscn").instantiate()
	get_root().add_child(room)
	for _frame in 15:
		await process_frame
	room.position_structure_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	camera = room.get_node("ReviewCamera") as Camera3D

	_set_game_view()
	room.set_base_color_mode(false)
	room.set_joint_variant(0)
	await _capture("game_r2_lit", "Unchanged gameplay camera; r2 continuous-wall candidate, original lighting")
	room.set_joint_variant(1)
	await _capture("game_r3_lit", "Unchanged gameplay camera; r3 wide-joint candidate, original lighting")
	room.set_joint_variant(0)
	room.set_base_color_mode(true)
	await _capture("game_r2_base_color", "Unchanged gameplay camera; r2 continuous-wall Base Color diagnostic")
	room.set_joint_variant(1)
	await _capture("game_r3_base_color", "Unchanged gameplay camera; r3 wide-joint Base Color diagnostic")

	_set_technical_view()
	room.set_base_color_mode(false)
	room.set_joint_variant(0)
	await _capture("technical_r2_lit", "Temporary close technical camera; r2 continuous wall, original lighting")
	room.set_joint_variant(1)
	await _capture("technical_r3_lit", "Temporary close technical camera; r3 wide joints, original lighting")
	room.set_joint_variant(0)
	room.set_base_color_mode(true)
	await _capture("technical_r2_base_color", "Temporary close technical camera; r2 continuous-wall Base Color diagnostic")
	room.set_joint_variant(1)
	await _capture("technical_r3_base_color", "Temporary close technical camera; r3 wide-joint Base Color diagnostic")

	_set_game_view()
	room.set_base_color_mode(false)
	room.set_joint_variant(0)
	var roundtrip := await _capture("game_r2_after_n_roundtrip", "Unchanged gameplay camera; N Base Color true-to-false restoration, returned to r2 continuous candidate")
	_assert_r2_roundtrip(roundtrip)

	var wall_material: ShaderMaterial = room.structure_materials["Wall_left"][0]
	FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify({
		"scene": "room1_wall_joints_r3.tscn",
		"geometry": room.baked_geometry_path,
		"irradiance": room.irradiance_path,
		"sample_world_m": SAMPLE,
		"wall_patch_size_px": [256, 272],
		"scope": "Independent left-wall 3.2 m albedo candidate. r2 shader, floor patch, r4 UV2/lightmap, geometry, lamps and camera are retained.",
		"final_wall_map": (wall_material.get_shader_parameter("wall_structure_map") as Texture2D).resource_path,
		"captures": records,
	}))
	print("ROOM1_WALL_JOINTS_R3_COMPARE_COMPLETE")
	quit()
