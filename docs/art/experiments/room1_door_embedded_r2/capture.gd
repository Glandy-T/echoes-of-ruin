extends SceneTree

const OUTPUT := "res://docs/art/experiments/room1_door_embedded_r2/evidence/"

func _initialize() -> void:
	call_deferred("capture")

func shot(name: String) -> void:
	for i in 15:
		await process_frame
	await RenderingServer.frame_post_draw
	assert(root.get_texture().get_image().save_png(OUTPUT + name + ".png") == OK)

func capture() -> void:
	var room = load("res://scenes/dev/room1_door_embedded_review_r2.tscn").instantiate()
	root.add_child(room)
	for i in 30:
		await process_frame
	room.info.get_parent().visible = false
	room.review_ui.pause_button.visible = false
	room.review_ui.close_dialogue()
	room.chip_enabled = false
	room.teleport_player(Vector3(10.5, 0.05, -7.7))
	await create_timer(0.5).timeout
	await shot("closed")
	var toggle := InputEventKey.new()
	toggle.physical_keycode = KEY_L
	toggle.pressed = true
	room._unhandled_key_input(toggle)
	await shot("lights_off")
	room._unhandled_key_input(toggle)
	await process_frame
	room.chip_enabled = true
	await create_timer(0.8).timeout
	await shot("scan")
	await create_timer(4.0).timeout
	await shot("open")
	print("Saved r2 embedded-door closed, scan, and open views")
	quit()
