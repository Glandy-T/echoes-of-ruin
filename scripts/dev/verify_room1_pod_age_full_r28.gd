extends Node

const REPORT := "res://docs/art/experiments/room1_pod_age_full_r28/source/runtime_validation.json"
const CAPTURE_REPORT := "res://docs/art/experiments/room1_pod_age_full_r28/source/capture_validation.json"
const EVIDENCE := "res://docs/art/experiments/room1_pod_age_full_r28/evidence/"
const ROLES := ["lid", "shell_side", "shell_end"]
const SIZES := {"lid": Vector2i(96, 184), "shell_side": Vector2i(184, 56), "shell_end": Vector2i(96, 56)}
var room: Node3D
var checks: Dictionary = {}
var errors: Array[String] = []
var baseline: Dictionary = {}

func _ready() -> void: call_deferred("run")
func wait_frames(count: int) -> void:
	for _i in count: await get_tree().process_frame
func check(label: String, ok: bool) -> void:
	checks[label] = ok
	if not ok: errors.append(label); push_error("R28_CHECK " + label)
func texture_path(texture: Texture2D) -> String: return texture.resource_path if texture else ""

func exterior_maps() -> Dictionary:
	var result := {}
	for id: String in room.room_pod_finishes:
		for entry: Dictionary in (room.room_pod_finishes[id] as RefCounted).entries:
			if ROLES.has(str(entry.role)):
				result[id + "/" + str(entry.role)] = texture_path((entry.material as ShaderMaterial).get_shader_parameter("color_map") as Texture2D)
	return result

func uv_signature() -> Dictionary:
	var result := {}
	for id: String in room.room_pods:
		var pod := room.room_pods[id] as Node3D
		for mesh: MeshInstance3D in pod.get_model_root().find_children("*", "MeshInstance3D", true, false):
			var surfaces := []
			for surface in mesh.mesh.get_surface_count():
				var arrays := mesh.mesh.surface_get_arrays(surface)
				surfaces.append([(arrays[Mesh.ARRAY_TEX_UV] as PackedVector2Array).to_byte_array().hex_encode().sha256_text(), (arrays[Mesh.ARRAY_TEX_UV2] as PackedVector2Array).to_byte_array().hex_encode().sha256_text()])
			result[id + ":" + str(mesh.get_path())] = surfaces
	return result

func protected_state() -> Dictionary:
	var result := {"lights": {}, "pods": {}}
	for light: Light3D in room.find_children("*", "Light3D", true, false):
		result.lights[str(light.get_path())] = [str(light.global_transform), light.light_energy, str(light.light_color), light.visible]
	for id: String in room.room_pods:
		var pod := room.room_pods[id] as Node3D
		var display := pod.get_display_mesh() as MeshInstance3D
		var material := display.get_active_material(0) as ShaderMaterial
		result.pods[id] = [str(pod.global_transform), pod.get_state_name(), pod.glass_visible, pod.screen_powered, texture_path(material.get_shader_parameter("screen_pixels") as Texture2D)]
	return result

func source_pixel_md5(path: String) -> String:
	var source := Image.load_from_file(ProjectSettings.globalize_path(path))
	return source.get_data().hex_encode().md5_text() if source else ""

func import_source_md5(path: String) -> String:
	var import_path := ProjectSettings.globalize_path(path + ".import")
	if not FileAccess.file_exists(import_path): return ""
	var ctex_regex := RegEx.new()
	ctex_regex.compile("res://([^\\\"]+\\.ctex)")
	var ctex := ctex_regex.search(FileAccess.get_file_as_string(import_path))
	if not ctex: return ""
	var cache_md5 := ProjectSettings.globalize_path("res://" + ctex.get_string(1).trim_suffix(".ctex") + ".md5")
	if not FileAccess.file_exists(cache_md5): return ""
	var regex := RegEx.new()
	regex.compile("source_md5=\\\"([0-9a-f]+)\\\"")
	var found := regex.search(FileAccess.get_file_as_string(cache_md5))
	return found.get_string(1) if found else ""

func final_import_validation() -> Dictionary:
	room.set_r28_mode(2)
	var runtime: Dictionary = room.get_r28_runtime_map_info()
	var maps := {}
	var ok := true
	for item in room._layout_entries():
		for role: String in ROLES:
			var path := str((item.maps as Dictionary).get(role, ""))
			var source_md5 := FileAccess.get_md5(ProjectSettings.globalize_path(path))
			var imported_md5 := import_source_md5(path)
			maps[str(item.id) + "/" + role] = {"source_png_md5": source_md5, "import_source_md5": imported_md5, "runtime": runtime.get(str(item.id) + "/" + role, {})}
			ok = ok and not source_md5.is_empty() and source_md5 == imported_md5
	return {"all_source_md5_match_import": ok, "maps": maps}

func capture_aba_validation() -> Dictionary:
	var a := EVIDENCE + "1_game_front_left.png"
	var b := EVIDENCE + "2_game_front_left.png"
	var restored := EVIDENCE + "1_restore_game_front_left.png"
	var sha_a := FileAccess.get_sha256(ProjectSettings.globalize_path(a))
	var sha_b := FileAccess.get_sha256(ProjectSettings.globalize_path(b))
	var sha_restored := FileAccess.get_sha256(ProjectSettings.globalize_path(restored))
	return {"A_r27_baseline": sha_a, "B_r28_candidate": sha_b, "A_restore": sha_restored, "A_differs_from_B": not sha_a.is_empty() and sha_a != sha_b, "A_equals_restore": not sha_a.is_empty() and sha_a == sha_restored}

func capture_png_count() -> int:
	var count := 0
	for file in DirAccess.get_files_at(ProjectSettings.globalize_path(EVIDENCE)):
		if file.ends_with(".png"): count += 1
	return count

func verify_candidate() -> void:
	var runtime: Dictionary = room.get_r28_runtime_map_info()
	for item in room._layout_entries():
		var id := str(item.id)
		check("number_" + id, int(item.number) == int(id.trim_prefix("P")))
		for role: String in ROLES:
			var path := str((item.maps as Dictionary).get(role, ""))
			var actual: Dictionary = runtime.get(id + "/" + role, {})
			var expected: Vector2i = SIZES[role]
			check("path_" + id + "_" + role, str(actual.get("path", "")) == path)
			check("size_" + id + "_" + role, int(actual.get("width", 0)) == expected.x and int(actual.get("height", 0)) == expected.y)
			check("decode_" + id + "_" + role, str(actual.get("decoded_pixel_md5", "")) == source_pixel_md5(path))

func check_mode(mode: int) -> void:
	room.set_r28_mode(mode)
	check("mode_" + str(mode), int(room.get_pod_age_r28_report().mode) == mode)
	check("only_color_map_" + str(mode), room.get_pod_age_r28_report().mutated_uniforms == ["color_map"])
	check("uv_" + str(mode), uv_signature() == baseline.uv)
	check("protected_" + str(mode), protected_state() == baseline.protected)
	if mode == 1: check("baseline_maps_" + str(mode), exterior_maps() == baseline.maps)
	else: verify_candidate()

func run() -> void:
	room = get_parent() as Node3D
	await wait_frames(18)
	room.finish_exit(); room.review_ui.close_dialogue()
	check("r28_assets_present", room._r28_assets_available())
	check("exactly_60_bindings", room.r28_snapshots.size() == 60)
	room.set_r28_mode(1)
	baseline = {"maps": exterior_maps(), "uv": uv_signature(), "protected": protected_state()}
	for mode in [1, 2, 1]: check_mode(mode)
	check("aba_baseline_restored", exterior_maps() == baseline.maps)
	var p12 := room.room_pods["P12"] as Node3D
	for opened in [false, true]:
		p12.set_open_immediate(opened); room._sync_complete_room_pose()
		var state := protected_state()
		for mode in [1, 2, 1]:
			room.set_r28_mode(mode)
			check(("open" if opened else "closed") + "_protected_" + str(mode), protected_state() == state)
	p12.set_open_immediate(false); room._sync_complete_room_pose(); room.set_r28_mode(2)
	var report := {"result": "PASS" if errors.is_empty() else "FAIL", "errors": errors, "checks": checks, "scope": "r28 ABA verifies exactly 60 exterior color_map bindings from layout_variants.json; source PNG decoded pixels, imported Texture2D sizes, maps, all20 UVs, lights, glass/screens, numbering and P12 open/closed remain controlled."}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REPORT.get_base_dir()))
	FileAccess.open(REPORT, FileAccess.WRITE).store_string(JSON.stringify(report, "\t"))
	var capture_validation := {"result": "PASS" if errors.is_empty() else "FAIL", "asset_import": final_import_validation(), "capture": {"driver": "opengl3", "resolution": [1280, 720], "png_count": capture_png_count(), "aba_game_front_left": capture_aba_validation()}, "runtime_verification": "PASS" if errors.is_empty() else "FAIL"}
	FileAccess.open(CAPTURE_REPORT, FileAccess.WRITE).store_string(JSON.stringify(capture_validation, "\t"))
	print("R28_POD_RUNTIME ", report.result, " checks=", checks.size(), " errors=", JSON.stringify(errors))
	get_tree().quit(0 if errors.is_empty() else 1)
