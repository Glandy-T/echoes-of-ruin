extends "res://scripts/dev/capture_room1_door_light_review_v1.gd"
# Same cameras as door light review v1: current (4) vs direction B (5).
const OUT_B := "res://docs/art/experiments/room1_door_light_recess_b1/evidence/"

func shot_l(name: String) -> void:
	sync_room()
	await frames(10)
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.save_png(OUT_B + name + ".png") == OK)
	records.append({"file": name + ".png", "light_mode": room.light_mode, "feedback": room.get("feedback_state"), "door_fraction": room.get("door_fraction"), "camera": str(camera.global_transform), "fov": camera.fov})
	print("B_SHOT ", name)

func capture() -> void:
	room = get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_B))
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
	for mode in [4, 5]:
		room.set_light_mode(mode)
		var tag := "current_r18" if mode == 4 else "b_recess"
		set_open(0.22); room.call("_update_feedback")
		look(Vector3(7.9, 1.45, -4.55), Vector3(10.55, 1.32, -9.2), 47.0)
		await shot_l("oblique_opening_" + tag)
		set_open(1.0); room.call("_update_feedback")
		await both("open_pass_" + tag)
		look(Vector3(7.8, 1.35, -4.55), Vector3(10.5, 1.15, -9.2), 50.0)
		await shot_l("oblique_open_" + tag)
	set_closed_idle(); room.call("_update_feedback")
	await both("idle_b_recess")
	FileAccess.open(OUT_B + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify({"shots": records}, "\t"))
	get_tree().quit()
