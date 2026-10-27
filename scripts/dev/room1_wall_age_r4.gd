extends "res://scripts/dev/room1_wall_joints_r3.gd"

# r4 keeps r3's construction joints byte-for-byte.  This switch isolates only
# the strength and placement of the wall's age treatment; it must not touch the
# floor, geometry, baked lighting, camera, or the pod-specific shaders.
const R3_WALL_MAP := preload("res://assets/art/room1_wall_joints_r3/wall_sample.png")
const AGED_WALL_MAP := preload("res://assets/art/room1_wall_age_r4/wall_sample.png")
const AGED_WALL_NAME := "Wall_left"

# 0 = the approved r3 joints with its light age treatment; 1 = r4's
# moderate-strength aging over the same joints.  r4 opens on the candidate.
var age_variant := 1

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	set_age_variant(age_variant)

func set_age_variant(variant: int) -> void:
	age_variant = clampi(variant, 0, 1)
	var selected_map: Texture2D = AGED_WALL_MAP if age_variant == 1 else R3_WALL_MAP
	var selected: Array = structure_materials.get(AGED_WALL_NAME, [])
	for material: ShaderMaterial in selected:
		material.set_shader_parameter("wall_structure_map", selected_map)
	# Keep r2's retained wall+floor shader mode.  In particular, do not call
	# r3.set_joint_variant(): it would overwrite this age-map selection on M.
	set_structure_mode(3)
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_M:
		set_age_variant(1 - age_variant)
		get_viewport().set_input_as_handled()
		return
	# r2 still owns N (Base Color diagnostic) and J (review reset).
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		var variant_label := "r4 中等强度旧化" if age_variant == 1 else "r3 轻旧化接缝"
		var diagnostic := " · Base Color检查" if base_color_mode else ""
		info.text = "Room 1 / 左墙旧化候选 r4 · %s%s\nM切换r3轻旧化/r4中等旧化 · N颜色基线 · J回观察点 · H说明 · WASD移动\n仅左墙3.2m样段替换贴图；地面、模型、灯光、布局、接缝像素和r4烘焙不变。" % [variant_label, diagnostic]
