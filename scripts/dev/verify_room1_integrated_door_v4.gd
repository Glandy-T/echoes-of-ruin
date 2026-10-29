extends Node

const REPORT := "res://docs/art/experiments/room1_integrated_door_v4/runtime_validation.json"
var errors: Array[String] = []


func _ready() -> void:
	call_deferred("_run")


func _run() -> void:
	var room := get_parent() as Node3D
	for i in 5:
		await get_tree().physics_frame
	room.call("finish_exit")
	room.set_process(false)
	room.set_physics_process(false)
	var frame := room.get("frame_material") as StandardMaterial3D
	var panel := room.get("door_mesh") as MeshInstance3D
	var root := room.get_node_or_null("IntegratedDoorV3") as Node3D
	if not frame or not panel or not root:
		errors.append("door panel or integrated jamb missing")
		_finish()
		return
	var jambs := root.find_children("JambLight_*", "MeshInstance3D", true, false)
	if jambs.size() != 4:
		errors.append("four jamb diffuser sides required")
	room.set("door_occupied", false)
	room.set("scan_complete", false)
	room.set("pass_valid", false)
	room.set("chip_enabled", true)
	room.set("door_fraction", 0.0)
	room.call("_update_feedback")
	if frame.albedo_color.g > 0.2:
		errors.append("standby diffuser emitted green")
	for jamb: MeshInstance3D in jambs:
		if not jamb.visible:
			errors.append("standby diffuser structure disappeared")
	room.set("door_occupied", true)
	room.call("_update_feedback")
	if str(room.get("feedback_state")) != "scanning" or frame.albedo_color.g > 0.2:
		errors.append("scanning lit passage ring")
	room.set("scan_complete", true)
	room.set("pass_valid", true)
	room.set("door_fraction", 0.2)
	room.call("_update_feedback")
	if str(room.get("feedback_state")) != "pass" or frame.albedo_color.g < 0.45:
		errors.append("authorized ring failed to turn green")
	room.set("pass_valid", false)
	room.set("chip_enabled", false)
	room.set("door_fraction", 0.0)
	room.call("_update_feedback")
	if str(room.get("feedback_state")) != "denied" or frame.albedo_color.g > 0.2:
		errors.append("denial incorrectly lit passage ring")
	_finish()


func _finish() -> void:
	var result := {"schema": "room1_integrated_door_v4_visual_check", "result": "PASS" if errors.is_empty() else "FAIL", "errors": errors, "standby_diffuser_visible_unlit": true, "jamb_sides": 4}
	print(JSON.stringify(result))
	var file := FileAccess.open(REPORT, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(result, "\t"))
	get_tree().quit(0 if errors.is_empty() else 1)
