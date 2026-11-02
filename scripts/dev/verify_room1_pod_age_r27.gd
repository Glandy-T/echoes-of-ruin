extends Node

const REPORT := "res://docs/art/experiments/room1_pod_age_r27/source/runtime_validation.json"
const R27_ROOT := "res://assets/art/room1_pod_age_r27/"
const R27_MAPS := {"lid": "lid.png", "shell_side": "shell_side.png", "shell_end": "shell_end.png"}
const R27_EXPECTED_SIZES := {"lid": Vector2i(96, 184), "shell_side": Vector2i(184, 56), "shell_end": Vector2i(96, 56)}

var room: Node3D
var checks: Dictionary = {}
var errors: Array[String] = []
var baseline: Dictionary = {}

func _ready() -> void:
	call_deferred("run")

func check(label: String, ok: bool) -> void:
	checks[label] = ok
	if not ok:
		errors.append(label)
		push_error("R27_CHECK " + label)

func frames(count: int) -> void:
	for _i in count:
		await get_tree().physics_frame

func texture_path(texture: Texture2D) -> String:
	return texture.resource_path if texture else ""

func pod_maps() -> Dictionary:
	var result: Dictionary = {}
	for id: String in room.room_pod_finishes:
		var entries: Array[Dictionary] = []
		for entry: Dictionary in (room.room_pod_finishes[id] as RefCounted).entries:
			var material := entry.material as ShaderMaterial
			entries.append({"role": str(entry.role), "map": texture_path(material.get_shader_parameter("color_map") as Texture2D), "shader": material.shader.resource_path})
		result[id] = entries
	return result

func p12_mesh_uv_signature() -> Dictionary:
	var result: Dictionary = {}
	var pod := room.room_pods["P12"] as Node3D
	for mesh: MeshInstance3D in pod.get_model_root().find_children("*", "MeshInstance3D", true, false):
		var surfaces: Array[Dictionary] = []
		for surface in mesh.mesh.get_surface_count():
			var arrays := mesh.mesh.surface_get_arrays(surface)
			surfaces.append({
				"mesh": mesh.mesh.resource_path,
				"uv0": (arrays[Mesh.ARRAY_TEX_UV] as PackedVector2Array).to_byte_array().hex_encode().sha256_text(),
				"uv2": (arrays[Mesh.ARRAY_TEX_UV2] as PackedVector2Array).to_byte_array().hex_encode().sha256_text(),
			})
		result[str(mesh.get_path())] = surfaces
	return result

func lights_state() -> Dictionary:
	var result: Dictionary = {}
	for node: Node in room.find_children("*", "Light3D", true, false):
		var light := node as Light3D
		result[str(node.get_path())] = {"transform": str(light.global_transform), "energy": light.light_energy, "color": str(light.light_color), "visible": light.visible}
	return result

func protected_p12_state() -> Dictionary:
	var pod := room.room_pods["P12"] as Node3D
	var display := pod.get_display_mesh() as MeshInstance3D
	var display_material := display.get_active_material(0) as ShaderMaterial
	var screen_texture := display_material.get_shader_parameter("screen_pixels") as Texture2D
	return {
		"pod_transform": str(pod.global_transform),
		"screen_shader": display_material.shader.resource_path,
		"screen_pixels": texture_path(screen_texture),
		"screen_powered": pod.screen_powered,
		"glass_visible": pod.glass_visible,
		"state": pod.get_state_name(),
	}

func exact_entries_equal(left: Dictionary, right: Dictionary, ignored_p12_roles: bool = false) -> bool:
	for id: String in left:
		if not right.has(id) or (left[id] as Array).size() != (right[id] as Array).size():
			return false
		for index in range((left[id] as Array).size()):
			var a: Dictionary = left[id][index]
			var b: Dictionary = right[id][index]
			if ignored_p12_roles and id == "P12" and R27_MAPS.has(str(a.role)):
				if str(a.role) != str(b.role) or str(a.shader) != str(b.shader):
					return false
			elif a != b:
				return false
	return true

func verify_candidate_maps() -> void:
	var maps := pod_maps()
	var runtime_maps: Dictionary = room.get_r27_runtime_map_info()
	for entry: Dictionary in maps["P12"]:
		var role := str(entry.role)
		if R27_MAPS.has(role):
			check("p12_candidate_" + role, str(entry.map) == R27_ROOT + str(R27_MAPS[role]))
			var runtime: Dictionary = runtime_maps[role]
			var expected: Vector2i = R27_EXPECTED_SIZES[role]
			check("runtime_size_" + role, int(runtime.width) == expected.x and int(runtime.height) == expected.y)
			check("runtime_pixels_" + role, not str(runtime.decoded_pixel_md5).is_empty())

func check_mode(mode: int) -> void:
	room.set_r27_mode(mode)
	var report: Dictionary = room.get_pod_age_r27_report()
	check("mode_" + str(mode), int(report.mode) == mode)
	check("only_color_map_" + str(mode), report.mutated_uniforms == ["color_map"])
	check("mesh_uv_" + str(mode), p12_mesh_uv_signature() == baseline.mesh_uv)
	check("lights_" + str(mode), lights_state() == baseline.lights)
	check("screen_glass_transform_" + str(mode), protected_p12_state() == baseline.protected)
	check("all_other_pod_bindings_" + str(mode), exact_entries_equal(pod_maps(), baseline.pods, mode == 2))
	if mode == 2:
		verify_candidate_maps()

func run() -> void:
	room = get_parent() as Node3D
	await frames(12)
	room.finish_exit()
	room.review_ui.close_dialogue()
	check("r27_assets_present", room._r27_assets_available())
	check("p12_exterior_captured", not room.r27_p12_snapshots.is_empty())
	room.set_r27_mode(1)
	baseline = {
		"pods": pod_maps(),
		"mesh_uv": p12_mesh_uv_signature(),
		"lights": lights_state(),
		"protected": protected_p12_state(),
	}
	for mode: int in [1, 2, 1]:
		check_mode(mode)
	check("aba_r26_p12_restored", pod_maps() == baseline.pods)
	var hero := room.room_pods["P12"] as Node3D
	for opened: bool in [false, true]:
		hero.set_open_immediate(opened)
		room._sync_complete_room_pose()
		var protected_before := protected_p12_state()
		for mode: int in [1, 2, 1]:
			room.set_r27_mode(mode)
			check(("open" if opened else "closed") + "_protected_" + str(mode), protected_p12_state() == protected_before)
	hero.set_open_immediate(false)
	room._sync_complete_room_pose()
	room.set_r27_mode(2)
	var report: Dictionary = {
		"result": "PASS" if errors.is_empty() else "FAIL",
		"errors": errors,
		"checks": checks,
		"scope": "r27 A/B/A changes only P12 lid, shell_side and shell_end color_map bindings. The r26 room remains the baseline: P12 mesh UVs, all lights, screen, glass, number-bearing source maps, P12 open/closed state and the other 19 pods are verified unchanged.",
	}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(REPORT.get_base_dir()))
	FileAccess.open(REPORT, FileAccess.WRITE).store_string(JSON.stringify(report, "\t"))
	print("R27_POD_RUNTIME ", report.result, " checks=", checks.size(), " errors=", JSON.stringify(errors))
	get_tree().quit(0 if errors.is_empty() else 1)
