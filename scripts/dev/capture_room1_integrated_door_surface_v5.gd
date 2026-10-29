extends Node

const OUT := "res://docs/art/experiments/room1_integrated_door_surface_v5/evidence/"


func _ready() -> void:
	call_deferred("_capture")


func _capture() -> void:
	var room := get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for i in 8:
		await get_tree().process_frame
	room.call("finish_exit")
	room.call("teleport_player", Vector3(10.5, 0.05, -7.7))
	for i in 8:
		await get_tree().process_frame
	var paper := room.get("paper_hero") as Sprite3D
	var bloom_paper := room.get("bloom_paper_hero") as Sprite3D
	if paper:
		paper.visible = false
	if bloom_paper:
		bloom_paper.visible = false
	var info := room.get("info") as Label
	if info:
		info.get_parent().visible = false
	var review_ui := room.get("review_ui") as Node
	var pause_button := review_ui.get("pause_button") as Control
	if pause_button:
		pause_button.visible = false
	room.set_process(false)
	room.set_physics_process(false)
	var original := room.get("door_closed_position") as Vector3
	var body_original := room.get("body_closed_position") as Vector3
	var panel := room.get("door_mesh") as MeshInstance3D
	var body := room.get("door_body") as StaticBody3D

	room.set("chip_enabled", true)
	room.set("door_occupied", false)
	room.set("scan_complete", false)
	room.set("pass_valid", false)
	room.set("door_fraction", 0.0)
	panel.global_position = original
	body.global_position = body_original
	room.call("_update_feedback")
	await _save("idle_closed.png")

	room.set("door_occupied", true)
	for i in 40:
		room.call("_update_feedback")
		if (room.get("status_material") as StandardMaterial3D).albedo_color.r > 0.6:
			break
		await get_tree().process_frame
	await _save("yellow_scanning.png")

	room.set("scan_complete", true)
	room.set("pass_valid", true)
	room.set("door_fraction", 0.2)
	panel.global_position = original + Vector3(0.304, 0, 0)
	body.global_position = body_original + Vector3(0.304, 0, 0)
	room.call("_update_feedback")
	await _save("green_opening.png")

	room.set("door_fraction", 1.0)
	panel.global_position = original + Vector3(1.52, 0, 0)
	body.global_position = body_original + Vector3(1.52, 0, 0)
	room.call("_update_feedback")
	await _save("green_open.png")

	room.set("door_fraction", 0.0)
	panel.global_position = original
	body.global_position = body_original
	room.set("pass_valid", false)
	room.set("chip_enabled", false)
	room.set("door_occupied", true)
	room.call("_update_feedback")
	await _save("red_denied_window_only.png")
	get_tree().quit()


func _save(name: String) -> void:
	for i in 10:
		await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	if image == null:
		push_error("A visible Godot window is required for screenshot " + name)
		get_tree().quit(1)
		return
	var error := image.save_png(OUT + name)
	print("DOOR_SHOT ", name, " ", image.get_width(), "x", image.get_height(), " err=", error)
	if error != OK:
		get_tree().quit(1)
