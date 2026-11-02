extends Node

const OUT := "res://docs/art/experiments/room1_pod_age_r27/evidence/"
const POD_DIAGNOSTIC := preload("res://scripts/dev/pod_color_diagnostic_r16.gdshader")

var room: Node3D
var camera: Camera3D
var hero: Node3D
var records: Array[Dictionary] = []
var diagnostic_snapshots: Array[Dictionary] = []
var overlays_frozen := false

func _ready() -> void:
	call_deferred("capture")

func look(position: Vector3, target: Vector3, fov: float) -> void:
	camera.global_position = position
	camera.look_at(target, Vector3.UP)
	camera.fov = fov

func sync_room() -> void:
	room._sync_render_camera()
	room._sync_bloom_camera()
	room._sync_standard_visuals()
	room._sync_complete_room_pose()
	room._sync_complete_screen_sources()
	room._sync_door_glow()

func shot(name: String, diagnostic: bool = false) -> void:
	sync_room()
	for _i in 12:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.get_width() == 1280 and image.get_height() == 720, "r27 capture must stay at the approved 1280x720 review resolution.")
	assert(image.save_png(OUT + name + ".png") == OK)
	records.append({
		"file": name + ".png",
		"mode": room.r27_mode,
		"p12_pose": hero.get_state_name(),
		"camera": str(camera.global_transform),
		"fov": camera.fov,
		"resolution": [image.get_width(), image.get_height()],
		"diagnostic": diagnostic,
		"overlays_frozen": overlays_frozen,
		"runtime_maps": room.get_r27_runtime_map_info(),
	})
	print("R27_SHOT ", name)

func freeze_screen_overlays() -> void:
	for pod: Node3D in room.room_pods.values():
		var viewport := pod.get("_screen_viewport") as SubViewport
		if viewport:
			viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED
	overlays_frozen = true

func set_p12_base_color_diagnostic(enabled: bool) -> void:
	if enabled:
		diagnostic_snapshots.clear()
		for item: Dictionary in room.r27_p12_snapshots:
			var material := item.material as ShaderMaterial
			var parameters: Dictionary = {}
			for uniform: Dictionary in material.shader.get_shader_uniform_list():
				parameters[str(uniform.name)] = material.get_shader_parameter(str(uniform.name))
			diagnostic_snapshots.append({"material": material, "shader": material.shader, "parameters": parameters})
			material.shader = POD_DIAGNOSTIC
			material.set_shader_parameter("color_map", parameters["color_map"])
			material.set_shader_parameter("base_color", parameters["base_color"])
	else:
		for item: Dictionary in diagnostic_snapshots:
			var material := item.material as ShaderMaterial
			material.shader = item.shader
			for key: String in item.parameters:
				material.set_shader_parameter(key, item.parameters[key])
		diagnostic_snapshots.clear()

func game_near_p12(prefix: String, opened: bool) -> void:
	hero.set_open_immediate(opened)
	room.teleport_player(Vector3(3.525, 0.05, -4.75))
	await get_tree().process_frame
	await shot(prefix + "game_near_p12_" + ("open" if opened else "closed"))

func close_views(prefix: String) -> void:
	hero.set_open_immediate(false)
	await game_near_p12(prefix, false)
	look(Vector3(1.775, 1.8, -4.45), Vector3(3.65, 0.43, -7.65), 44.0)
	await shot(prefix + "p12_three_quarter_closed")
	look(Vector3(1.8, 1.6, -7.1), Vector3(3.525, 0.35, -7.65), 55.0)
	await shot(prefix + "p12_long_side_closed")
	look(Vector3(2.15, 1.22, -8.9), Vector3(3.525, 0.53, -8.29), 48.0)
	await shot(prefix + "p12_end_closed")

func open_views(prefix: String) -> void:
	hero.set_open_immediate(true)
	await game_near_p12(prefix, true)
	look(Vector3(1.775, 1.8, -4.45), Vector3(3.65, 0.43, -7.65), 44.0)
	await shot(prefix + "p12_three_quarter_open")
	look(Vector3(1.7, 1.55, -6.9), Vector3(3.525, 0.82, -7.65), 52.0)
	await shot(prefix + "p12_inner_lid_open")

func capture() -> void:
	room = get_parent() as Node3D
	assert(room._r27_assets_available(), "r27 capture requires all three P12 exterior maps.")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for _i in 120:
		await get_tree().process_frame
	room.finish_exit()
	room.review_ui.close_dialogue()
	room.actor_shadow_on = false
	room._sync_actor_shadow()
	for _i in 60:
		await get_tree().process_frame
	for key: String in ["paper_hero", "bloom_paper_hero"]:
		var actor := room.get(key) as Sprite3D
		if actor:
			actor.visible = false
	room.info.get_parent().hide()
	if room.review_ui.get("pause_button"):
		(room.review_ui.get("pause_button") as Control).hide()
	camera = room.get_node("ReviewCamera") as Camera3D
	hero = room.room_pods["P12"] as Node3D
	freeze_screen_overlays()
	room.set_process(false)
	room.set_physics_process(false)
	for mode: int in [1, 2]:
		room.set_r27_mode(mode)
		await close_views(str(mode) + "_")
		await open_views(str(mode) + "_")
	# An unlit material read is a temporary diagnostic only; it restores every
	# shader/parameter immediately afterwards and is never written to the scene.
	room.set_r27_mode(2)
	hero.set_open_immediate(false)
	set_p12_base_color_diagnostic(true)
	look(Vector3(1.775, 1.8, -4.45), Vector3(3.65, 0.43, -7.65), 44.0)
	await shot("2_basecolor_three_quarter_closed", true)
	hero.set_open_immediate(true)
	look(Vector3(1.7, 1.55, -6.9), Vector3(3.525, 0.82, -7.65), 52.0)
	await shot("2_basecolor_inner_lid_open", true)
	set_p12_base_color_diagnostic(false)
	room.set_r27_mode(1)
	hero.set_open_immediate(false)
	look(Vector3(1.775, 1.8, -4.45), Vector3(3.65, 0.43, -7.65), 44.0)
	await shot("1_restore_three_quarter_closed")
	room.set_r27_mode(2)
	FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify(records, "\t"))
	get_tree().quit()
