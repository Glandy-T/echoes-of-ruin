extends "res://scripts/dev/room1_integrated_door_v3.gd"

# Reuse v3 face shading, motion, collision and access states. Only the pixel
# surface and unlit reveal finish are changed for this visual comparison.
const DOOR_FINISH_V6 := preload("res://assets/art/room1_integrated_door_finish_v6/door_front.png")
const UNLIT_REVEAL := preload("res://scripts/dev/room1_integrated_door_finish_v6_reveal.gdshader")
var neutral_reveal: ShaderMaterial
var neutral_leaf_side: ShaderMaterial


func _replace_placeholder() -> void:
	super._replace_placeholder()
	panel_material.set_shader_parameter("pixel_map", DOOR_FINISH_V6)
	# The visible 85 mm side of the leaf should belong to the same material
	# family, not read as a black accessory fixed around the opening.
	neutral_reveal = ShaderMaterial.new()
	neutral_reveal.shader = UNLIT_REVEAL
	neutral_reveal.set_shader_parameter("tint_color", Vector3(0.110, 0.140, 0.130))
	neutral_leaf_side = ShaderMaterial.new()
	neutral_leaf_side.shader = UNLIT_REVEAL
	neutral_leaf_side.set_shader_parameter("tint_color", Vector3(0.060, 0.083, 0.080))
	door_mesh.set_surface_override_material(1, neutral_leaf_side)


func _update_feedback() -> void:
	super._update_feedback()
	if not is_instance_valid(frame_material) or not is_instance_valid(integrated_root):
		return
	if feedback_state == "pass":
		for part: MeshInstance3D in integrated_root.find_children("JambLight_*", "MeshInstance3D", true, false):
			part.material_override = frame_material
			part.visible = true
		return  # Keep v3's full four-sided green passage ring.
	# Three sides of the *unlit* inset diffuser remain visible as neutral
	# construction. Hide the bottom segment: v4 proved that a lit-looking line
	# against the dark floor reads as a spurious light source.
	for part: MeshInstance3D in integrated_root.find_children("JambLight_*", "MeshInstance3D", true, false):
		part.visible = part.name != "JambLight_Bottom"
		part.material_override = neutral_reveal


func _update_info() -> void:
	super._update_info()
	if info:
		info.text = "Room 1 / 一体化门门框与旧化 v6 · 审图\n待机三边窄收口、底边无亮线；门面保留 v3 光照，仅换接触点旧化贴图\nWASD移动 · F1走廊 · F2西梯 · F3一层梯间 · R回房间。"
