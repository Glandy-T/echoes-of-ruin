extends Node

const EVIDENCE := "res://docs/art/experiments/cryo_building_room1_route_v3/evidence/"


func _ready() -> void:
	call_deferred("_capture")


func _capture() -> void:
	var level := get_parent() as Node3D
	for i in 5:
		await get_tree().process_frame
	level.call("finish_exit")
	level.call("teleport_player", Vector3(9.2, 0.05, -8.6))
	level.set("door_occupied", true)
	level.set("scan_complete", true)
	level.set("door_fraction", 1.0)
	var door_mesh := level.get("door_mesh") as MeshInstance3D
	var door_body := level.get("door_body") as StaticBody3D
	var closed := level.get("door_closed_position") as Vector3
	var body_closed := level.get("body_closed_position") as Vector3
	if door_mesh and door_body:
		door_mesh.global_position = closed + Vector3(1.52, 0, 0)
		door_body.global_position = body_closed + Vector3(1.52, 0, 0)
	var paper := level.get("paper_hero") as Sprite3D
	var bloom_paper := level.get("bloom_paper_hero") as Sprite3D
	if paper:
		paper.visible = false # reveal the doorway in the static review image
	if bloom_paper:
		bloom_paper.visible = false
	for i in 10:
		await get_tree().process_frame
	_save("room1_open_door_to_corridor.png")
	if paper:
		paper.visible = true
	if bloom_paper:
		bloom_paper.visible = true
	level.call("teleport_player", Vector3(-1.2, 0.05, -20.0))
	for i in 10:
		await get_tree().process_frame
	_save("west_corridor_4f.png")
	level.call("teleport_player", Vector3(-1.2, 0.05, -36.5))
	for i in 10:
		await get_tree().process_frame
	_save("west_stair_entry_4f.png")
	level.call("teleport_player", Vector3(-1.5, -11.35, -38.9))
	for i in 10:
		await get_tree().process_frame
	_save("west_stair_landing_1f.png")
	# An elevated structural screenshot supplements the inherited shallow game
	# camera, which cannot reveal the U-shaped stair from its corridor viewpoint.
	level.set_process(false)
	var camera := level.get_node("ReviewCamera") as Camera3D
	camera.global_position = Vector3(-1.3, 10.0, -39.0)
	camera.look_at(Vector3(-1.3, -0.2, -39.0), Vector3.FORWARD)
	level.call("_sync_render_camera")
	for i in 10:
		await get_tree().process_frame
	_save("west_stair_structure_4f.png")
	get_tree().quit()


func _save(name: String) -> void:
	var image := get_viewport().get_texture().get_image()
	if image == null:
		push_error("Screenshot needs a visible Godot window: " + name)
		get_tree().quit(1)
		return
	var path := EVIDENCE + name
	print("SCREENSHOT ", name, " ", image.get_width(), "x", image.get_height(), " error=", image.save_png(path))
