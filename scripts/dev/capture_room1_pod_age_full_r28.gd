extends Node

const OUT := "res://docs/art/experiments/room1_pod_age_full_r28/evidence/"
const DIAGNOSTIC := preload("res://scripts/dev/pod_color_diagnostic_r16.gdshader")
var room: Node3D
var camera: Camera3D
var records: Array[Dictionary] = []
var diagnostic_snapshots: Array[Dictionary] = []

func _ready() -> void: call_deferred("capture")
func sync_room() -> void:
	room._sync_render_camera(); room._sync_bloom_camera(); room._sync_standard_visuals(); room._sync_complete_room_pose(); room._sync_complete_screen_sources(); room._sync_door_glow()
func look(position: Vector3, target: Vector3, fov: float = 46.0) -> void:
	camera.global_position = position; camera.look_at(target, Vector3.UP); camera.fov = fov
func shot(name: String, diagnostic: bool = false) -> void:
	sync_room()
	for _i in 12: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.get_width() == 1280 and image.get_height() == 720)
	assert(image.save_png(OUT + name + ".png") == OK)
	var p12 := room.room_pods["P12"] as Node3D
	records.append({"file": name + ".png", "mode": room.r28_mode, "p12_pose": p12.get_state_name(), "camera": str(camera.global_transform), "fov": camera.fov, "resolution": [1280, 720], "diagnostic": diagnostic, "runtime_maps": room.get_r28_runtime_map_info()})
	print("R28_SHOT ", name)
func freeze_overlays() -> void:
	for pod: Node3D in room.room_pods.values():
		var viewport := pod.get("_screen_viewport") as SubViewport
		if viewport: viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
func game_shot(name: String, player_position: Vector3) -> void:
	room.teleport_player(player_position)
	# Follow FOV belongs to the actual review camera, not the room controller.
	camera.fov = 50.0
	await get_tree().process_frame
	camera.fov = 50.0
	await shot(name)
func set_diagnostic(enabled: bool) -> void:
	if enabled:
		diagnostic_snapshots.clear()
		for item: Dictionary in room.r28_snapshots:
			var material := item.material as ShaderMaterial
			var params := {}
			for uniform: Dictionary in material.shader.get_shader_uniform_list(): params[str(uniform.name)] = material.get_shader_parameter(str(uniform.name))
			diagnostic_snapshots.append({"material": material, "shader": material.shader, "parameters": params})
			material.shader = DIAGNOSTIC; material.set_shader_parameter("color_map", params["color_map"]); material.set_shader_parameter("base_color", params["base_color"])
	else:
		for item: Dictionary in diagnostic_snapshots:
			var material := item.material as ShaderMaterial; material.shader = item.shader
			for key: String in item.parameters: material.set_shader_parameter(key, item.parameters[key])
		diagnostic_snapshots.clear()
func pod_closeup(id: String, suffix: String = "closed") -> void:
	var pod := room.room_pods[id] as Node3D
	# The inspection camera stays in the central circulation zone.  A direct
	# local offset would push P10/P11 through an exterior wall.
	look(Vector3(clampf(pod.global_position.x - 1.6, 0.55, 20.45), 1.8, -4.65), pod.global_position + Vector3(0.0, 0.44, 0.0), 44.0)
	await shot("2_pod_" + id.to_lower() + "_exterior_" + suffix)
func first_variant(letter: String) -> String:
	for item in room._layout_entries():
		if str(item.get("lid_variant", "")).to_lower() == letter: return str(item.id)
	return "P12"
func used_non_a_lid_variants() -> Array[String]:
	var variants: Array[String] = []
	for item in room._layout_entries():
		var variant := str(item.get("lid_variant", "")).to_lower()
		if not variant.is_empty() and variant != "a" and not variants.has(variant): variants.append(variant)
	variants.sort()
	return variants

func capture() -> void:
	room = get_parent() as Node3D
	assert(room._r28_assets_available(), "r28 capture needs an imported 20-pod layout and maps")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for _i in 120: await get_tree().process_frame
	room.finish_exit(); room.review_ui.close_dialogue(); room.actor_shadow_on = false; room._sync_actor_shadow()
	# A/B gameplay coverage always begins closed.  P12 alone is opened later in
	# explicitly named diagnostic frames; the remaining nineteen never open.
	(room.room_pods["P12"] as Node3D).set_open_immediate(false)
	room._sync_complete_room_pose()
	for key: String in ["paper_hero", "bloom_paper_hero"]:
		var actor := room.get(key) as Sprite3D
		if actor: actor.visible = false
	room.info.get_parent().hide(); camera = room.get_node("ReviewCamera") as Camera3D
	freeze_overlays(); room.set_process(false); room.set_physics_process(false)
	var game_views := [
		{"name": "front_left", "position": Vector3(3.0, 0.05, -3.8)},
		{"name": "front_middle", "position": Vector3(8.2, 0.05, -3.8)},
		{"name": "front_right", "position": Vector3(14.8, 0.05, -3.8)},
		{"name": "back_left", "position": Vector3(3.0, 0.05, -7.8)},
		{"name": "back_middle", "position": Vector3(8.2, 0.05, -7.8)},
		{"name": "back_right", "position": Vector3(14.8, 0.05, -7.8)},
	]
	for mode in [1, 2]:
		room.set_r28_mode(mode)
		for view in game_views: await game_shot(str(mode) + "_game_" + str(view.name), view.position)
	room.set_r28_mode(2)
	# One unobstructed technical view per physical pod, with its local axes used
	# so mirrored pairs remain readable instead of being hidden by foreground pods.
	for index in 20: await pod_closeup("P%02d" % (index + 1))
	var corners := [
		{"name": "front_left", "camera": Vector3(0.7, 1.1, -1.4), "target": Vector3(0.25, 0.02, -0.25)},
		{"name": "front_right", "camera": Vector3(20.25, 1.1, -1.4), "target": Vector3(20.75, 0.02, -0.25)},
		{"name": "back_left", "camera": Vector3(0.7, 1.1, -8.3), "target": Vector3(0.25, 0.02, -9.25)},
		{"name": "back_right", "camera": Vector3(20.25, 1.1, -8.3), "target": Vector3(20.75, 0.02, -9.25)},
	]
	for corner in corners:
		look(corner.camera, corner.target, 55.0); await shot("2_corner_" + str(corner.name))
	var p12 := room.room_pods["P12"] as Node3D
	p12.set_open_immediate(false); await pod_closeup("P12", "p12_closed")
	p12.set_open_immediate(true); await pod_closeup("P12", "p12_open"); p12.set_open_immediate(false)
	# Non-P12 pods intentionally remain closed.  Their baked GI has no matching
	# open-cover solution yet.  The final layout, rather than a hardcoded list,
	# determines which approved non-A variants receive representative checks.
	for letter in used_non_a_lid_variants():
		var id := first_variant(letter); await pod_closeup(id, "variant_" + letter + "_closed")
	set_diagnostic(true)
	look(Vector3(10.5, 28.0, -4.75), Vector3(10.5, 0.0, -4.74), 48.0); await shot("2_basecolor_overview", true)
	set_diagnostic(false)
	room.set_r28_mode(1); await game_shot("1_restore_game_front_left", game_views[0].position); room.set_r28_mode(2)
	FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify(records, "\t"))
	get_tree().quit()
