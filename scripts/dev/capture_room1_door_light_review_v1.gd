extends "res://scripts/dev/capture_room1_door_shader_r31.gd"

# Door light review v1: the existing r17 inner jamb core and r18 soft glow,
# re-captured on the confirmed r32 door.  No light, colour or timing is
# changed here; this only records every feedback state for the user to judge.
const OUT_L := "res://docs/art/experiments/room1_door_light_review_v1/evidence/"
const GAME := Vector3(10.5, 0.05, -4.75)

func shot_l(name: String) -> void:
	sync_room()
	await frames(10)
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.save_png(OUT_L + name + ".png") == OK)
	records.append({"file": name + ".png", "feedback": room.get("feedback_state"), "door_fraction": room.get("door_fraction"),
		"door_glow_on": room.get("door_glow_on"), "door": room.get_r32_door_report(), "camera": str(camera.global_transform), "fov": camera.fov})
	print("LIGHT_SHOT ", name)

func game_view() -> void:
	room.teleport_player(GAME)
	room.update_follow_camera()
	camera.fov = 50.0
	await frames(1)

func near_view() -> void:
	look(Vector3(10.5, 1.48, -4.85), Vector3(10.5, 1.28, -9.2), 47.0)

func set_denied() -> void:
	room.set("chip_enabled", false)
	room.set("door_occupied", true)
	room.set("scan_complete", false)
	room.set("pass_valid", false)
	room.set("door_fraction", 0.0)
	room.get("door_mesh").global_position = room.get("door_closed_position")
	room.get("door_body").global_position = room.get("body_closed_position")
	room.call("_update_feedback")

func wait_flash(on: bool) -> void:
	# The scanning window flashes on a 0.5 s cycle (0.30 s lit).
	while (fmod(float(Time.get_ticks_msec()) / 1000.0, 0.5) < 0.30) != on:
		await get_tree().process_frame
	room.call("_update_feedback")

func both(name: String) -> void:
	await game_view()
	await shot_l("game_" + name)
	near_view()
	await shot_l("near_" + name)

func capture() -> void:
	room = get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_L))
	await frames(120)
	room.finish_exit(); room.review_ui.close_dialogue()
	room.actor_shadow_on = false; room._sync_actor_shadow()
	freeze_overlays()
	for key: String in ["paper_hero", "bloom_paper_hero"]:
		var actor := room.get(key) as Sprite3D
		if actor: actor.visible = false
	room.info.get_parent().hide()
	camera = room.get_node("ReviewCamera") as Camera3D
	room.set_process(false); room.set_physics_process(false)
	room.set_r32_mode(3)
	room.set_door_glow(true)

	set_closed_idle()
	await both("1_idle")
	set_scanning(); await wait_flash(true)
	await both("2_scanning_lit")
	set_scanning(); await wait_flash(false)
	near_view(); await shot_l("near_2_scanning_dark_phase")
	set_denied()
	await both("3_denied_red")
	for glow in [false, true]:
		room.set_door_glow(glow)
		var tag := "r18_soft" if glow else "r17_core"
		set_open(0.22)
		look(Vector3(7.9, 1.45, -4.55), Vector3(10.55, 1.32, -9.2), 47.0)
		await shot_l("oblique_4_opening_" + tag)
		set_open(1.0)
		await both("5_open_pass_" + tag)
	room.set_door_glow(true)
	FileAccess.open(OUT_L + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify({"shots": records}, "\t"))
	get_tree().quit()
