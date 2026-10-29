extends Node

const REPORT := "res://docs/art/experiments/room1_integrated_door_pixellab_v7/runtime_validation.json"
var errors: Array[String] = []


func _ready() -> void:
	call_deferred("_run")


func _run() -> void:
	var room := get_parent() as Node3D
	for i in 5:
		await get_tree().physics_frame
	room.call("finish_exit")
	var integrated := room.get("integrated_root") as Node3D
	var panel := room.get("door_mesh") as MeshInstance3D
	var frame := room.get("frame_material") as StandardMaterial3D
	var neutral := room.get("neutral_reveal") as ShaderMaterial
	if not integrated or not panel or not frame or not neutral:
		_finish()
		return
	var jambs := integrated.find_children("JambLight_*", "MeshInstance3D", true, false)
	if jambs.size() != 4:
		errors.append("passage ring does not contain four jamb segments")
	var pixel_map := (panel.get_surface_override_material(0) as ShaderMaterial).get_shader_parameter("pixel_map") as Texture2D
	if not pixel_map or pixel_map.resource_path != "res://assets/art/room1_integrated_door_pixellab_v7/door_front.png":
		errors.append("v6 pixel map is not installed")
	room.set("door_occupied", false)
	room.set("chip_enabled", true)
	room.set("scan_complete", false)
	room.set("pass_valid", false)
	room.call("_update_feedback")
	_check_unlit(jambs, neutral, "idle")
	room.set("door_occupied", true)
	room.call("_update_feedback")
	_check_unlit(jambs, neutral, "scanning")
	room.set("scan_complete", true)
	room.set("pass_valid", true)
	room.call("_update_feedback")
	if str(room.get("feedback_state")) != "pass":
		errors.append("authorized passage state missing")
	for jamb: MeshInstance3D in jambs:
		if not jamb.visible or jamb.material_override != frame:
			errors.append("passage does not restore green lamp: " + jamb.name)
	room.set("chip_enabled", false)
	room.set("pass_valid", false)
	room.call("_update_feedback")
	if str(room.get("feedback_state")) != "denied":
		errors.append("denial state missing")
	_check_unlit(jambs, neutral, "denied")
	_finish()


func _check_unlit(jambs: Array[Node], neutral: ShaderMaterial, state: String) -> void:
	for jamb: MeshInstance3D in jambs:
		var expected := jamb.name != "JambLight_Bottom"
		if jamb.visible != expected or jamb.material_override != neutral:
			errors.append(state + " unlit reveal mismatch: " + jamb.name)


func _finish() -> void:
	var report := {"schema": "room1_integrated_door_pixellab_v7", "result": "PASS" if errors.is_empty() else "FAIL", "errors": errors,
		"unlit_bottom_segment": false, "green_passage_segments": 4}
	print(JSON.stringify(report))
	var file := FileAccess.open(REPORT, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "\t"))
	get_tree().quit(0 if errors.is_empty() else 1)
