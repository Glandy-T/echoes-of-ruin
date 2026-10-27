extends SceneTree

const OUT := "res://docs/art/experiments/room1_surface_structure_r2/evidence/"
const SAMPLE := {
	"wall": {"plane_x": 0.2, "z": [-6.4, -3.2], "height": [0.0, 3.4]},
	"floor": {"x": [0.2, 3.4], "z": [-6.4, -3.2]},
}

var room: Node
var camera: Camera3D
var records: Array = []

func _initialize() -> void:
	call_deferred("capture")

func _capture(name: String, description: String) -> void:
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
		"mode": room.structure_mode,
		"base_color_preview": room.base_color_mode,
	})

func _set_game_view() -> void:
	room.teleport_player(Vector3(3.525, 0.0, -4.75))
	room._sync_render_camera()
	room._sync_bloom_camera()

func _set_technical_view() -> void:
	# Capture-only review view: wide enough to prove the complete 3.4 m wall
	# span (lamp groove through protection band), the floor handoff, and one pod.
	# It deliberately never writes the gameplay camera transform back to the scene.
	camera.global_position = Vector3(5.75, 2.65, -1.35)
	camera.look_at(Vector3(0.2, 1.55, -4.8), Vector3.UP)
	camera.fov = 60.0
	room._sync_render_camera()
	room._sync_bloom_camera()

func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	room = load("res://scenes/dev/room1_surface_structure_r2.tscn").instantiate()
	get_root().add_child(room)
	for _frame in 15:
		await process_frame
	room.position_structure_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	camera = room.get_node("ReviewCamera") as Camera3D

	_set_game_view()
	for mode in 4:
		room.set_structure_mode(mode)
		room.set_base_color_mode(false)
		await _capture("game_%02d_%s" % [mode, ["baseline", "wall", "floor", "both"][mode]], "Unchanged gameplay camera, original exposure")
	room.set_structure_mode(0)
	room.set_base_color_mode(true)
	await _capture("game_baseline_base_color", "Unchanged gameplay camera, original-material Base Color diagnostic")
	room.set_structure_mode(3)
	room.set_base_color_mode(true)
	await _capture("game_04_both_base_color", "Unchanged gameplay camera, Base Color diagnostic")
	# Regression proof: N must restore every r2/r3 receiver shader and uniform
	# before the ordinary comparison continues.
	room.set_structure_mode(0)
	room.set_base_color_mode(false)
	await _capture("game_baseline_after_n_roundtrip", "Unchanged gameplay camera, original-material baseline after N true-to-false restoration")

	_set_technical_view()
	for mode in [0, 3]:
		room.set_structure_mode(mode)
		room.set_base_color_mode(false)
		await _capture("technical_%s" % ["baseline", "both"][1 if mode == 3 else 0], "Temporary close technical camera; wall lamp groove, protection band, floor and one pod in frame")
	room.set_structure_mode(0)
	room.set_base_color_mode(true)
	await _capture("technical_baseline_base_color", "Temporary close technical camera; original-material Base Color diagnostic")
	room.set_structure_mode(3)
	room.set_base_color_mode(true)
	await _capture("technical_both_base_color", "Temporary close technical camera; Base Color diagnostic")

	var bindings := {}
	for mesh_name in room.structure_materials:
		var values: Array = []
		for material: ShaderMaterial in room.structure_materials[mesh_name]:
			values.append({
				"kind": material.get_shader_parameter("structure_kind"),
				"wall_map": (material.get_shader_parameter("wall_structure_map") as Texture2D).resource_path,
				"floor_map": (material.get_shader_parameter("floor_structure_map") as Texture2D).resource_path,
				"lightmap": (material.get_shader_parameter("strip_irradiance") as Texture2D).resource_path,
				"continuous_diffuser": material.get_shader_parameter("uniform_strip_emission"),
				"diffuser_scale": material.get_shader_parameter("diffuser_radiance_scale"),
			})
		bindings[mesh_name] = values
	FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify({
		"scene": "room1_surface_structure_r2.tscn",
		"geometry": room.baked_geometry_path,
		"irradiance": room.irradiance_path,
		"sample_world_m": SAMPLE,
		"patch_size_px": {"wall": [256, 272], "floor": [256, 256]},
		"scope": "Independent local colour-patch candidate. Existing r4 UV2/lightmap and emitter parameters retained; Base Color captures are diagnostics only.",
		"bindings": bindings,
		"captures": records,
	}))
	print("ROOM1_STRUCTURE_R2_COMPARE_COMPLETE")
	quit()
