extends Node

const REPORT := "res://docs/art/experiments/room1_door_window_r30/source/runtime_validation.json"
const CAPTURE_REPORT := "res://docs/art/experiments/room1_door_window_r30/source/capture_validation.json"
const EVIDENCE := "res://docs/art/experiments/room1_door_window_r30/evidence/"
const R30_DOOR := "res://assets/art/room1_door_window_r30/door_front.png"
const R30_SIZE := Vector2i(112, 184)
var room: Node3D
var checks: Dictionary = {}
var errors: Array[String] = []
var baseline: Dictionary = {}

func _ready() -> void:
	call_deferred("run")

func frames(count: int) -> void:
	for _i in count: await get_tree().process_frame

func check(label: String, ok: bool) -> void:
	checks[label] = ok
	if not ok:
		errors.append(label)
		push_error("R30_CHECK " + label)

func texture_path(texture: Texture2D) -> String:
	return texture.resource_path if texture else ""

func source_pixel_md5(path: String) -> String:
	var source := Image.load_from_file(ProjectSettings.globalize_path(path))
	return source.get_data().hex_encode().md5_text() if source else ""

func import_source_md5(path: String) -> String:
	var import_path := ProjectSettings.globalize_path(path + ".import")
	if not FileAccess.file_exists(import_path): return ""
	var ctex_regex := RegEx.new(); ctex_regex.compile("res://([^\\\"]+\\.ctex)")
	var ctex := ctex_regex.search(FileAccess.get_file_as_string(import_path))
	if not ctex: return ""
	var cache_md5 := ProjectSettings.globalize_path("res://" + ctex.get_string(1).trim_suffix(".ctex") + ".md5")
	if not FileAccess.file_exists(cache_md5): return ""
	var regex := RegEx.new(); regex.compile("source_md5=\\\"([0-9a-f]+)\\\"")
	var found := regex.search(FileAccess.get_file_as_string(cache_md5))
	return found.get_string(1) if found else ""

func uv_signature(mesh: MeshInstance3D) -> Array:
	var result: Array = []
	for surface in mesh.mesh.get_surface_count():
		var arrays := mesh.mesh.surface_get_arrays(surface)
		# The door GLB deliberately omits a second UV channel on one surface.
		# Preserve that fact in the signature instead of coercing null into UV data.
		var uv: Variant = arrays[Mesh.ARRAY_TEX_UV]
		var uv2: Variant = arrays[Mesh.ARRAY_TEX_UV2]
		var uv_hash := (uv as PackedVector2Array).to_byte_array().hex_encode().sha256_text() if uv is PackedVector2Array else "<none>"
		var uv2_hash := (uv2 as PackedVector2Array).to_byte_array().hex_encode().sha256_text() if uv2 is PackedVector2Array else "<none>"
		result.append([uv_hash, uv2_hash])
	return result

func protected_state() -> Dictionary:
	var result := {"lights": {}, "pods": {}, "wall_floor": {}, "door": {}}
	for light: Light3D in room.find_children("*", "Light3D", true, false):
		result.lights[str(light.get_path())] = [str(light.global_transform), light.light_energy, str(light.light_color), light.visible]
	for id: String in room.room_pods:
		var pod := room.room_pods[id] as Node3D
		var display := pod.get_display_mesh() as MeshInstance3D
		var material := display.get_active_material(0) as ShaderMaterial
		result.pods[id] = [str(pod.global_transform), pod.get_state_name(), pod.glass_visible, pod.screen_powered, texture_path(material.get_shader_parameter("screen_pixels") as Texture2D)]
	for name: String in room.full_materials:
		if name in ["Floor_continuous_no_tile_seams", "Wall_left", "Wall_right", "Wall_front", "Wall_rear_left", "Wall_rear_right", "Wall_rear_door_header"]:
			var paths: Array[String] = []
			for material: ShaderMaterial in room.full_materials[name]: paths.append(texture_path(material.get_shader_parameter("color_map") as Texture2D))
			result.wall_floor[name] = paths
	var panel := room.get("door_mesh") as MeshInstance3D
	result.door = [str(panel.global_transform), str(panel.mesh), uv_signature(panel), str(room.get("feedback_state")), room.get("door_fraction")]
	return result

func capture_aba_validation() -> Dictionary:
	var a := EVIDENCE + "1_a_game_door_closed.png"
	var b := EVIDENCE + "2_b_game_door_closed.png"
	var restore := EVIDENCE + "1_a_restore_game_door_closed.png"
	var sha_a := FileAccess.get_sha256(ProjectSettings.globalize_path(a))
	var sha_b := FileAccess.get_sha256(ProjectSettings.globalize_path(b))
	var sha_restore := FileAccess.get_sha256(ProjectSettings.globalize_path(restore))
	return {"A_r29": sha_a, "B_r30": sha_b, "A_restore": sha_restore, "A_differs_from_B": not sha_a.is_empty() and sha_a != sha_b, "A_equals_restore": not sha_a.is_empty() and sha_a == sha_restore}

func capture_png_count() -> int:
	var count := 0
	for file in DirAccess.get_files_at(ProjectSettings.globalize_path(EVIDENCE)):
		if file.ends_with(".png"): count += 1
	return count

func test_door_behavior() -> void:
	room.finish_exit(); room.set("chip_enabled", true); room.set("door_occupied", false); room.set("scan_complete", false); room.set("pass_valid", false); room.call("_update_feedback")
	check("idle_state_preserved", str(room.get("feedback_state")) == "idle")
	room.set("door_occupied", true); room.call("_update_feedback")
	check("yellow_scan_preserved", str(room.get("feedback_state")) == "scanning")
	room.set("scan_complete", true); room.set("pass_valid", true); room.set("door_fraction", 1.0); room.call("_update_feedback")
	check("authorized_green_preserved", str(room.get("feedback_state")) == "pass")

func check_mode(mode: int) -> void:
	room.set_r30_mode(mode)
	var runtime: Dictionary = room.get_r30_door_runtime_info()
	check("mode_" + str(mode), int(runtime.mode) == mode)
	check("only_pixel_map_" + str(mode), room.get_r30_door_report().mutated_uniforms == ["pixel_map"])
	check("protected_" + str(mode), protected_state() == baseline.protected)
	if mode == 1:
		check("a_map_restored", str(runtime.path) == str(baseline.a_path))
	else:
		check("b_path", str(runtime.path) == R30_DOOR)
		check("b_size", int(runtime.width) == R30_SIZE.x and int(runtime.height) == R30_SIZE.y)
		check("b_decoded_pixels", str(runtime.decoded_pixel_md5) == source_pixel_md5(R30_DOOR))
		check("b_source_md5_matches_import", FileAccess.get_md5(ProjectSettings.globalize_path(R30_DOOR)) == import_source_md5(R30_DOOR))

func run() -> void:
	room = get_parent() as Node3D
	await frames(24)
	check("r30_asset_imported", room._r30_asset_available())
	check("r30_single_binding_ready", room.r30_ready and room.r30_baseline_map != null)
	if not errors.is_empty():
		finish(); return
	room.set_r30_mode(1)
	baseline = {"a_path": room.get_r30_door_runtime_info().path, "protected": protected_state()}
	for mode in [1, 2, 1]: check_mode(mode)
	check("aba_a_restored", str(room.get_r30_door_runtime_info().path) == str(baseline.a_path))
	test_door_behavior()
	room.set_r30_mode(2)
	finish()

func finish() -> void:
	var runtime: Dictionary = room.get_r30_door_runtime_info() if room else {}
	var report := {"schema": "room1_door_window_r30", "result": "PASS" if errors.is_empty() else "FAIL", "errors": errors, "checks": checks, "runtime": runtime, "scope": "ABA validates only DoorPanel pixel_map. Existing r28 pods, wall/floor maps, lights, mesh UV, authorization feedback and door behavior are protected."}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REPORT.get_base_dir()))
	FileAccess.open(REPORT, FileAccess.WRITE).store_string(JSON.stringify(report, "\t"))
	var capture := {"result": "PASS" if errors.is_empty() else "FAIL", "asset_import": {"source_png_md5": FileAccess.get_md5(ProjectSettings.globalize_path(R30_DOOR)) if FileAccess.file_exists(ProjectSettings.globalize_path(R30_DOOR)) else "", "import_source_md5": import_source_md5(R30_DOOR), "runtime": runtime}, "capture": {"driver": "opengl3", "resolution": [1280, 720], "png_count": capture_png_count(), "aba_closed_idle": capture_aba_validation()}, "runtime_verification": "PASS" if errors.is_empty() else "FAIL"}
	FileAccess.open(CAPTURE_REPORT, FileAccess.WRITE).store_string(JSON.stringify(capture, "\t"))
	print("R30_DOOR_RUNTIME ", report.result, " checks=", checks.size(), " errors=", JSON.stringify(errors))
	get_tree().quit(0 if errors.is_empty() else 1)
