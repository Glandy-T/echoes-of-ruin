extends Node

const REPORT := "res://docs/art/experiments/room1_integrated_door_v3/runtime_validation.json"
var errors: Array[String] = []


func _ready() -> void:
	call_deferred("_run")


func _run() -> void:
	var room := get_parent() as Node3D
	for i in 5:
		await get_tree().physics_frame
	room.call("finish_exit")
	var panel := room.get("door_mesh") as MeshInstance3D
	var solid := room.get("door_body") as StaticBody3D
	var status := room.get("status_material") as StandardMaterial3D
	var frame := room.get("frame_material") as StandardMaterial3D
	var actor := room.get("player") as CharacterBody3D
	var integrated := room.get_node_or_null("IntegratedDoorV3") as Node3D
	if not panel or not solid or not status or not frame or not integrated or not actor:
		errors.append("integrated door, collision, window, frame, or player missing")
		_finish({"result": "FAIL", "errors": errors})
		return
	if integrated.find_children("JambLight_*", "MeshInstance3D", true, false).size() != 4:
		errors.append("inner jamb ring is not four continuous sides")
	if room.get("scan_line") != null:
		errors.append("old full-door scan line still exists")
	var old := room.get_node_or_null("Solid_MAIN_DOOR_PLACEHOLDER_NOT_APPROVED") as StaticBody3D
	if old and old.collision_layer != 0:
		errors.append("old door collider remains active")
	if str(room.get("feedback_state")) != "idle":
		errors.append("door did not start idle")

	room.call("teleport_player", Vector3(10.5, 0.05, -8.6))
	for i in 36:
		await get_tree().physics_frame
	var yellow := str(room.get("feedback_state")) == "scanning"
	var ring_during_scan := frame.albedo_color
	if not yellow:
		errors.append("approach did not begin chip scan")
	if ring_during_scan.g > 0.3:
		errors.append("jamb lit during yellow scan")
	for i in 330:
		await get_tree().physics_frame
	var green := str(room.get("feedback_state")) == "pass"
	var opened := float(room.get("door_fraction"))
	var origin := room.get("door_closed_position") as Vector3
	var panel_offset := panel.global_position.x - origin.x
	var solid_offset := solid.global_position.x - (room.get("body_closed_position") as Vector3).x
	if not green or opened < 0.95:
		errors.append("authorized passage did not open with green feedback")
	if absf(panel_offset - solid_offset) > 0.001:
		errors.append("door panel and collider slide are not synchronized")
	if frame.albedo_color.g < 0.45 or status.albedo_color.g < 0.55:
		errors.append("status window or full inner-jamb ring failed to show green")

	room.set("test_mode", true)
	room.set("test_input", Vector2(0, -1))
	for i in 110:
		await get_tree().physics_frame
	room.set("test_input", Vector2.ZERO)
	var crossed := actor.global_position
	if crossed.z > -10.0 or absf(crossed.y) > 0.3:
		errors.append("player could not cross new door into 4F corridor")
	for i in 270:
		await get_tree().physics_frame
	var closed_again := float(room.get("door_fraction"))
	if closed_again > 0.05 or str(room.get("feedback_state")) != "idle":
		errors.append("green passage feedback did not reset after closing")

	room.set("chip_enabled", false)
	room.call("teleport_player", Vector3(10.5, 0.05, -8.6))
	for i in 18:
		await get_tree().physics_frame
	var denied := str(room.get("feedback_state")) == "denied"
	if not denied or status.albedo_color.r < 0.5:
		errors.append("unauthorized chip did not show red in the small window")
	if frame.albedo_color.r > 0.2 or frame.albedo_color.g > 0.3:
		errors.append("inner jamb incorrectly turned red/green in one-actor denial")
	if float(room.get("door_fraction")) > 0.05:
		errors.append("door opened for unauthorized chip")

	_finish({
		"schema": "room1_integrated_door_v3_runtime_check",
		"result": "PASS" if errors.is_empty() else "FAIL",
		"errors": errors,
		"jamb_sides": 4,
		"scan_state": yellow,
		"open_state": green,
		"open_fraction": opened,
		"panel_collider_offset_difference_m": absf(panel_offset - solid_offset),
		"crossed_to_corridor": crossed.z < -10.0,
		"closed_fraction_after_pass": closed_again,
		"denied_window_red": denied,
		"red_jamb_state_implemented": false,
		"second_actor_simulated": false
	})


func _finish(report: Dictionary) -> void:
	print(JSON.stringify(report))
	var file := FileAccess.open(REPORT, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "\t"))
	get_tree().quit(0 if errors.is_empty() else 1)
