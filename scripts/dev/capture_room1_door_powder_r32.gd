extends "res://scripts/dev/capture_room1_door_shader_r31.gd"

# r32 review captures: A r30 / B r31 / C r32 from identical cameras, then C's
# authentication and open states, then an A/B/C -> A restore check.
const OUT32 := "res://docs/art/experiments/room1_door_powder_r32/evidence/"
const VIEWS := [
	["door_wall_front", Vector3(10.5, 1.2, -3.8), Vector3(10.5, 1.2, -9.2), 44.0],
	["door_wall_oblique", Vector3(7.7, 1.45, -4.65), Vector3(10.45, 1.35, -9.2), 47.0],
	["door_front_close", Vector3(9.05, 1.25, -6.35), Vector3(10.4, 1.28, -9.2), 52.0],
	["door_oblique_close", Vector3(12.15, 1.25, -6.25), Vector3(10.5, 1.25, -9.2), 52.0],
]

func shot32(name: String) -> void:
	sync_room()
	await frames(12)
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.get_width() == 1280 and image.get_height() == 720)
	assert(image.save_png(OUT32 + name + ".png") == OK)
	records.append({"file": name + ".png", "door": room.get_r32_door_report(),
		"feedback": room.get("feedback_state"), "door_fraction": room.get("door_fraction"),
		"camera": str(camera.global_transform), "fov": camera.fov})
	print("R32_SHOT ", name)

func game32(name: String) -> void:
	room.teleport_player(Vector3(10.5, 0.05, -4.75))
	room.update_follow_camera()
	camera.fov = 50.0
	await frames(1)
	await shot32(name)

func capture() -> void:
	room = get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT32))
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

	for mode in [1, 2, 3]:
		var prefix: String = {1: "1_a", 2: "2_b", 3: "3_c"}[mode]
		room.set_r32_mode(mode)
		set_closed_idle()
		await game32(prefix + "_game_door_closed")
		for v: Array in VIEWS:
			look(v[1], v[2], v[3])
			await shot32(prefix + "_" + v[0])

	room.set_r32_mode(3)
	set_scanning()
	look(Vector3(10.5, 1.48, -4.85), Vector3(10.5, 1.28, -9.2), 47.0)
	await shot32("3_c_scanning_yellow_window")
	set_open(0.22)
	look(Vector3(7.9, 1.45, -4.55), Vector3(10.55, 1.32, -9.2), 47.0)
	await shot32("3_c_opening_green_reveal")
	set_open(1.0)
	await game32("3_c_game_door_open")
	look(Vector3(10.5, 1.2, -3.8), Vector3(10.5, 1.15, -9.2), 47.0)
	await shot32("3_c_open_green_soft_glow")

	room.set_r32_mode(1)
	set_closed_idle()
	await game32("1_a_restore_game_door_closed")
	room.set_r32_mode(2)
	set_closed_idle()
	await game32("2_b_restore_game_door_closed")
	room.set_r32_mode(3)
	set_closed_idle()

	var sha := func(n: String) -> String: return FileAccess.get_sha256(ProjectSettings.globalize_path(OUT32 + n + ".png"))
	var validation := {
		"a_restore_identical_to_r30": sha.call("1_a_game_door_closed") == sha.call("1_a_restore_game_door_closed"),
		"b_restore_identical_to_r31": sha.call("2_b_game_door_closed") == sha.call("2_b_restore_game_door_closed"),
		"c_differs_from_a": sha.call("1_a_game_door_closed") != sha.call("3_c_game_door_closed"),
	}
	print("R32_VALIDATION ", JSON.stringify(validation))
	FileAccess.open(OUT32 + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify({"shots": records, "validation": validation}, "\t"))
	get_tree().quit()
