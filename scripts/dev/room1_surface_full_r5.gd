extends "res://scripts/dev/room1_wall_age_r4.gd"

const FULL_SHADER := preload("res://scripts/dev/room1_surface_full_r5.gdshader")
const FLOOR_AGED := preload("res://assets/art/room1_surface_full_r5/floor_aged.png")
const FLOOR_LEAKS := preload("res://assets/art/room1_surface_full_r5/floor_with_leaks.png")
const WALL_LEFT := preload("res://assets/art/room1_surface_full_r5/wall_left.png")
const WALL_RIGHT := preload("res://assets/art/room1_surface_full_r5/wall_right.png")
const WALL_FRONT := preload("res://assets/art/room1_surface_full_r5/wall_front.png")
const WALL_REAR := preload("res://assets/art/room1_surface_full_r5/wall_rear.png")

const TARGETS := {"Floor_continuous_no_tile_seams": 1, "Wall_left": 2, "Wall_right": 3, "Wall_front": 4, "Wall_rear_left": 5, "Wall_rear_right": 5, "Wall_rear_door_header": 5}
var full_materials: Dictionary = {}
var full_mode := 3

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint(): return
	for mesh_name: String in TARGETS:
		_install_full_material(mesh_name, TARGETS[mesh_name])
	set_full_surface_mode(full_mode)

func _copy_parameters(material: ShaderMaterial) -> Dictionary:
	var values := {}
	if material.shader:
		for uniform: Dictionary in material.shader.get_shader_uniform_list():
			var name := StringName(uniform.get("name", ""))
			if name != &"": values[name] = material.get_shader_parameter(name)
	return values

func _install_full_material(mesh_name: String, kind: int) -> void:
	var receiver := $Shell.find_child(mesh_name, true, false) as MeshInstance3D
	assert(receiver != null)
	var selected: Array[ShaderMaterial] = []
	for surface in receiver.mesh.get_surface_count():
		var material := receiver.get_active_material(surface) as ShaderMaterial
		if material == null: continue
		var before := _copy_parameters(material)
		var color := before.get(&"color_map") as Texture2D
		if color == null or color.get_width() <= 32: continue
		material.shader = FULL_SHADER
		for name: StringName in before:
			material.set_shader_parameter(name, before[name])
		material.set_shader_parameter("full_surface_kind", kind)
		material.set_shader_parameter("full_surface_mode", 0)
		material.set_shader_parameter("full_wall_left_map", WALL_LEFT)
		material.set_shader_parameter("full_wall_right_map", WALL_RIGHT)
		material.set_shader_parameter("full_wall_front_map", WALL_FRONT)
		material.set_shader_parameter("full_wall_rear_map", WALL_REAR)
		material.set_shader_parameter("full_floor_aged_map", FLOOR_AGED)
		material.set_shader_parameter("full_floor_leaks_map", FLOOR_LEAKS)
		# Only the inherited left/floor receivers retain r4 local-map sampling.
		if not before.has(&"structure_enabled"):
			material.set_shader_parameter("structure_enabled", 0.0)
			material.set_shader_parameter("structure_kind", 0)
			material.set_shader_parameter("base_color_preview", 0.0)
		selected.append(material)
	full_materials[mesh_name] = selected

func set_full_surface_mode(mode: int) -> void:
	full_mode = clampi(mode, 0, 3)
	for mesh_name in full_materials:
		for material: ShaderMaterial in full_materials[mesh_name]: material.set_shader_parameter("full_surface_mode", full_mode)
	_update_info()

func set_base_color_mode(enabled: bool) -> void:
	if enabled == base_color_mode: return
	base_color_mode = enabled
	if enabled: _enable_r5_base_color()
	else: _restore_r5_base_color()
	_update_info()

func _enable_r5_base_color() -> void:
	diagnostic_material_snapshots.clear()
	for material: ShaderMaterial in baked_receivers:
		if material.shader != FULL_SHADER:
			var parameters := _copy_parameters(material)
			diagnostic_material_snapshots.append({"material":material,"shader":material.shader,"parameters":parameters})
			material.shader = FULL_SHADER
			for name: StringName in parameters: material.set_shader_parameter(name, parameters[name])
			material.set_shader_parameter("structure_enabled", 0.0)
			material.set_shader_parameter("full_surface_mode", 0)
		material.set_shader_parameter("base_color_preview", 1.0)

func _restore_r5_base_color() -> void:
	for snapshot: Dictionary in diagnostic_material_snapshots:
		var material := snapshot["material"] as ShaderMaterial
		material.shader = snapshot["shader"] as Shader
		for name: StringName in snapshot["parameters"]: material.set_shader_parameter(name, snapshot["parameters"][name])
	diagnostic_material_snapshots.clear()
	for material: ShaderMaterial in baked_receivers:
		if material.shader == FULL_SHADER: material.set_shader_parameter("base_color_preview", 0.0)

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_M:
			set_full_surface_mode((full_mode + 1) % 4); get_viewport().set_input_as_handled(); return
		if event.physical_keycode == KEY_N:
			set_base_color_mode(not base_color_mode); get_viewport().set_input_as_handled(); return
		if event.physical_keycode == KEY_J:
			position_structure_review(); get_viewport().set_input_as_handled(); return
	# Do not hand M/N/J to r4/r3/r2: each has legacy material switches.
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		var labels := ["r4局部基线", "全墙差分", "全墙＋全地面旧化", "全墙＋漏液地面"]
		info.text = "Room 1 / 全室表面 r5 · %s%s\nM切换r4局部/全墙/无漏液地面/漏液地面 · N颜色基线 · J回观察点 · H说明 · WASD移动\n仅7个大色面替换；模型、布局、相机、灯光、舱内特殊着色器与r4 UV2烘焙均保持。" % [labels[full_mode], " · Base Color检查" if base_color_mode else ""]
