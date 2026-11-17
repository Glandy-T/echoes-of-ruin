extends "res://scripts/dev/capture_room1_door_light_review_v1.gd"
# Status window 1c: old v3 lamp quad vs dark-glass window aligned to the recess.
const OUT_G := "res://docs/art/experiments/room1_door_status_glass_v1/evidence/"

func shot_l(name: String) -> void:
	sync_room()
	await frames(10)
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.save_png(OUT_G + name + ".png") == OK)
	records.append({"file": name + ".png", "glass_on": room.glass_on, "feedback": room.get("feedback_state"), "camera": str(camera.global_transform), "fov": camera.fov})
	print("G_SHOT ", name)

func capture() -> void:
	room = get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_G))
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
	for glass in [false, true]:
		room.set_status_glass(glass)
		var tag := "glass" if glass else "old"
		set_closed_idle(); room.call("_update_feedback")
		await both("1_idle_" + tag)
		set_scanning(); await wait_flash(true)
		await both("2_scanning_" + tag)
		set_denied(); room.call("_update_feedback")
		await both("3_denied_" + tag)
		set_open(0.22); room.call("_update_feedback")
		look(Vector3(7.9, 1.45, -4.55), Vector3(10.55, 1.32, -9.2), 47.0)
		await shot_l("4_opening_green_" + tag)
	FileAccess.open(OUT_G + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify({"shots": records}, "\t"))
	get_tree().quit()
