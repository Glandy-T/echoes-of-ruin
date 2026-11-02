extends Node

# Deliberately separate from the play camera.  This scene is only a review
# driver; it never persists camera transforms into Room 1.
const OUT := "res://docs/art/experiments/room1_door_material_r29/evidence/"
var room: Node3D
var camera: Camera3D
var records: Array[Dictionary] = []

func _ready() -> void:
	call_deferred("capture")

func frames(count: int) -> void:
	for _i in count:
		await get_tree().process_frame

func sync_room() -> void:
	room._sync_render_camera()
	room._sync_bloom_camera()
	room._sync_standard_visuals()
	room._sync_complete_room_pose()
	room._sync_complete_screen_sources()
	room._sync_door_glow()

func look(position: Vector3, target: Vector3, fov: float = 46.0) -> void:
	camera.global_position = position
	camera.look_at(target, Vector3.UP)
	camera.fov = fov

func shot(name: String) -> void:
	sync_room()
	await frames(12)
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.get_width() == 1280 and image.get_height() == 720)
	assert(image.save_png(OUT + name + ".png") == OK)
	records.append({
		"file": name + ".png", "mode": room.r29_mode,
		"feedback": room.get("feedback_state"), "door_fraction": room.get("door_fraction"),
		"camera": str(camera.global_transform), "fov": camera.fov,
		"resolution": [1280, 720], "door_map": room.get_r29_door_runtime_info()
	})
	print("R29_SHOT ", name)

func set_closed_idle() -> void:
	room.set("chip_enabled", true)
	room.set("door_occupied", false)
	room.set("scan_complete", false)
	room.set("pass_valid", false)
	room.set("door_fraction", 0.0)
	room.get("door_mesh").global_position = room.get("door_closed_position")
	room.get("door_body").global_position = room.get("body_closed_position")
	room.call("_update_feedback")

func set_scanning() -> void:
	room.set("chip_enabled", true)
	room.set("door_occupied", true)
	room.set("scan_complete", false)
	room.set("pass_valid", false)
	room.set("door_fraction", 0.0)
	room.get("door_mesh").global_position = room.get("door_closed_position")
	room.get("door_body").global_position = room.get("body_closed_position")
	room.call("_update_feedback")

func set_open(fraction: float) -> void:
	room.set("chip_enabled", true)
	room.set("door_occupied", true)
	room.set("scan_complete", true)
	room.set("pass_valid", true)
	room.set("door_fraction", fraction)
	room.get("door_mesh").global_position = (room.get("door_closed_position") as Vector3) + Vector3(1.52 * fraction, 0, 0)
	room.get("door_body").global_position = (room.get("body_closed_position") as Vector3) + Vector3(1.52 * fraction, 0, 0)
	room.call("_update_feedback")

func game_shot(name: String, player_position: Vector3) -> void:
	room.teleport_player(player_position)
	room.update_follow_camera()
	camera.fov = 50.0
	await frames(1)
	await shot(name)

func freeze_overlays() -> void:
	# Keep the live pod monitor clocks out of closed-state A/B/A comparisons.
	for pod: Node3D in room.room_pods.values():
		var viewport := pod.get("_screen_viewport") as SubViewport
		if viewport:
			viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED

func capture() -> void:
	room = get_parent() as Node3D
	assert(room._r29_asset_available(), "r29 capture requires the final imported door_front.png")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	await frames(120)
	room.finish_exit()
	room.review_ui.close_dialogue()
	room.actor_shadow_on = false
	room._sync_actor_shadow()
	freeze_overlays()
	for key: String in ["paper_hero", "bloom_paper_hero"]:
		var actor := room.get(key) as Sprite3D
		if actor: actor.visible = false
	room.info.get_parent().hide()
	camera = room.get_node("ReviewCamera") as Camera3D
	room.set_process(false)
	room.set_physics_process(false)

	# Fixed-state A/B/A first: identical frame and closed idle state mean the
	# soft halo cannot be the reason a texture comparison differs.
	set_closed_idle()
	room.set_r29_mode(1)
	await game_shot("1_a_game_door_closed", Vector3(10.5, 0.05, -4.75))
	# The Room 1 portal is centered on the rear wall at z≈-9.2.  Keep all
	# technical review cameras inside the actual room bounds and face that door.
	look(Vector3(10.5, 1.2, -3.8), Vector3(10.5, 1.2, -9.2), 44.0)
	await shot("1_a_door_wall_front")
	look(Vector3(7.7, 1.45, -4.65), Vector3(10.45, 1.35, -9.2), 47.0)
	await shot("1_a_door_wall_oblique")

	room.set_r29_mode(2)
	set_closed_idle()
	await game_shot("2_b_game_door_closed", Vector3(10.5, 0.05, -4.75))
	look(Vector3(10.5, 1.2, -3.8), Vector3(10.5, 1.2, -9.2), 44.0)
	await shot("2_b_door_wall_front")
	look(Vector3(7.7, 1.45, -4.65), Vector3(10.45, 1.35, -9.2), 47.0)
	await shot("2_b_door_wall_oblique")
	look(Vector3(9.05, 1.25, -6.35), Vector3(10.4, 1.28, -9.2), 52.0)
	await shot("2_b_door_front_close")
	look(Vector3(12.15, 1.25, -6.25), Vector3(10.5, 1.25, -9.2), 52.0)
	await shot("2_b_door_oblique_close")

	set_scanning()
	look(Vector3(10.5, 1.48, -4.85), Vector3(10.5, 1.28, -9.2), 47.0)
	await shot("2_b_scanning_yellow_window")
	set_open(0.22)
	look(Vector3(7.9, 1.45, -4.55), Vector3(10.55, 1.32, -9.2), 47.0)
	await shot("2_b_opening_green_reveal")
	set_open(1.0)
	await game_shot("2_b_game_door_open", Vector3(10.5, 0.05, -4.75))
	look(Vector3(10.5, 1.2, -3.8), Vector3(10.5, 1.15, -9.2), 47.0)
	await shot("2_b_open_green_soft_glow")
	look(Vector3(7.8, 1.35, -4.55), Vector3(10.5, 1.15, -9.2), 50.0)
	await shot("2_b_open_oblique_close")

	room.set_r29_mode(1)
	set_closed_idle()
	await game_shot("1_a_restore_game_door_closed", Vector3(10.5, 0.05, -4.75))
	look(Vector3(10.5, 1.2, -3.8), Vector3(10.5, 1.2, -9.2), 44.0)
	await shot("1_a_restore_door_wall_front")
	room.set_r29_mode(2)
	set_closed_idle()
	FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify(records, "\t"))
	get_tree().quit()
