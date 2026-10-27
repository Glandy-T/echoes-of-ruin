extends "res://scripts/dev/room1_surface_structure_r2.gd"

# This candidate intentionally reuses r2's shader, receivers, lightmap and floor.
# Only the existing Wall_left 3.2 m sample gets a different albedo map.
const R2_WALL_MAP := preload("res://assets/art/room1_surface_structure_r2/wall_sample.png")
const JOINT_WALL_MAP := preload("res://assets/art/room1_wall_joints_r3/wall_sample.png")
const JOINT_WALL_NAME := "Wall_left"

# 0 = r2's continuous wall, 1 = r3's wide construction joints.
var joint_variant := 1

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	set_joint_variant(joint_variant)

func set_joint_variant(variant: int) -> void:
	joint_variant = clampi(variant, 0, 1)
	var selected_map: Texture2D = JOINT_WALL_MAP if joint_variant == 1 else R2_WALL_MAP
	var selected: Array = structure_materials.get(JOINT_WALL_NAME, [])
	for material: ShaderMaterial in selected:
		material.set_shader_parameter("wall_structure_map", selected_map)
	# Both variants deliberately remain in r2's wall+floor comparison mode so
	# M isolates the wall-joint decision instead of changing the floor too.
	super.set_structure_mode(3)
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_M:
		set_joint_variant(1 - joint_variant)
		get_viewport().set_input_as_handled()
		return
	# r2 continues to own N (Base Color diagnostic) and J (review reset).
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		var variant_label := "r3 宽幅模块接缝" if joint_variant == 1 else "r2 连续墙面"
		var diagnostic := " · Base Color检查" if base_color_mode else ""
		info.text = "Room 1 / 左墙接缝候选 r3 · %s%s\nM切换r2无缝/r3接缝 · N颜色基线 · J回观察点 · H说明 · WASD移动\n仅左墙3.2m样段替换贴图；地面、模型、灯光、布局和r4烘焙不变。" % [variant_label, diagnostic]
