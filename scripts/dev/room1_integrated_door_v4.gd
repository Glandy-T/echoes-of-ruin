extends "res://scripts/dev/room1_integrated_door_v3.gd"

# Rejected visual comparison only: the bottom looked self-lit and the whole
# leaf was brighter than the room. Use v3 as the current review baseline.
# Retained solely so the archived A/B capture remains reproducible.
const FACE_REVIEW_SHADER := preload("res://scripts/dev/room1_integrated_door_v4.gdshader")


func _replace_placeholder() -> void:
	super._replace_placeholder()
	panel_material.shader = FACE_REVIEW_SHADER
	# Keep the actual 85 mm side in the same mineral/metal family as the wall.
	# A narrow seal can stay dark; the entire side of the leaf should not be black.
	door_mesh.set_surface_override_material(1, _unshaded_color(Color(0.060, 0.083, 0.080)))


func _update_feedback() -> void:
	super._update_feedback()
	if not is_instance_valid(frame_material) or not is_instance_valid(integrated_root):
		return
	# The lamp is off, but its narrow built-in diffuser still exists physically.
	# Keep it an unlit structural reveal rather than a black empty cutout.
	if feedback_state != "pass":
		frame_material.albedo_color = Color(0.060, 0.085, 0.080)
	for part: MeshInstance3D in integrated_root.find_children("JambLight_*", "MeshInstance3D", true, false):
		part.visible = true


func _update_info() -> void:
	super._update_info()
	if info:
		info.text = "Room 1 / 一体化门色阶与收边 v4 · 审图\n门板略亮于墙；待机灯槽可见但熄灭；认证与单扇侧滑沿用 v3\nWASD移动 · F1走廊 · F2西梯 · F3一层梯间 · R回房间。"
