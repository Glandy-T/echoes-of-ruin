extends "res://scripts/dev/room1_pod_exit_animation_r3.gd"

const STRUCTURE_SHADER := preload("res://scripts/dev/room1_surface_structure_r2.gdshader")
const FLOOR_MAP := preload("res://assets/art/room1_surface_structure_r2/floor_sample.png")
const WALL_MAP := preload("res://assets/art/room1_surface_structure_r2/wall_sample.png")

const FLOOR_NAME := "Floor_continuous_no_tile_seams"
const WALL_NAME := "Wall_left"
const SAMPLE_ORIGIN := Vector3(0.2, 0.0, -6.4)
const SAMPLE_SIZE := Vector3(3.2, 3.4, 3.2)

var structure_mode := 3
var base_color_mode := false
var structure_materials: Dictionary = {}
# N is a diagnostic only.  These snapshots preserve the r2 lit-pod interior
# shaders and all of their current parameters while the common Base Color view
# is temporarily active.
var diagnostic_material_snapshots: Array[Dictionary] = []

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	# Keep every non-target receiver exactly on its inherited r3/r2 shader.  In
	# particular, P02/P12/P17 interiors carry their own window-light algorithm.
	_install_structure_patch(FLOOR_NAME, 1)
	_install_structure_patch(WALL_NAME, 2)
	set_structure_mode(structure_mode)
	call_deferred("position_structure_review")

func _install_structure_patch(mesh_name: String, kind: int) -> void:
	var receiver := $Shell.find_child(mesh_name, true, false) as MeshInstance3D
	assert(receiver != null)
	var selected: Array[ShaderMaterial] = []
	for surface in receiver.mesh.get_surface_count():
		var material := receiver.get_active_material(surface) as ShaderMaterial
		if material == null:
			continue
		var source_map := material.get_shader_parameter("color_map") as Texture2D
		# Do not touch the shell underside or small auxiliary receiver surfaces.
		if source_map == null or source_map.get_width() <= 32:
			continue
		material.shader = STRUCTURE_SHADER
		material.set_shader_parameter("wall_structure_map", WALL_MAP)
		material.set_shader_parameter("floor_structure_map", FLOOR_MAP)
		material.set_shader_parameter("structure_kind", kind)
		material.set_shader_parameter("structure_enabled", 0.0)
		material.set_shader_parameter("base_color_preview", 0.0)
		selected.append(material)
	structure_materials[mesh_name] = selected

func set_structure_mode(mode: int) -> void:
	structure_mode = clampi(mode, 0, 3)
	for mesh_name in structure_materials:
		var enabled: bool = structure_mode == 3 or (structure_mode == 1 and mesh_name == WALL_NAME) or (structure_mode == 2 and mesh_name == FLOOR_NAME)
		for material: ShaderMaterial in structure_materials[mesh_name]:
			material.set_shader_parameter("structure_enabled", 1.0 if enabled else 0.0)
	_update_info()

func set_base_color_mode(enabled: bool) -> void:
	if enabled == base_color_mode:
		return
	base_color_mode = enabled
	if base_color_mode:
		_enable_base_color_diagnostic()
	else:
		_restore_base_color_diagnostic()
	_update_info()

func _enable_base_color_diagnostic() -> void:
	diagnostic_material_snapshots.clear()
	for material: ShaderMaterial in baked_receivers:
		if material.shader != STRUCTURE_SHADER:
			var parameters: Dictionary = {}
			for uniform: Dictionary in material.shader.get_shader_uniform_list():
				var parameter_name := StringName(uniform.get("name", ""))
				if parameter_name != &"":
					parameters[parameter_name] = material.get_shader_parameter(parameter_name)
			diagnostic_material_snapshots.append({
				"material": material,
				"shader": material.shader,
				"parameters": parameters,
			})
			material.shader = STRUCTURE_SHADER
			material.set_shader_parameter("wall_structure_map", WALL_MAP)
			material.set_shader_parameter("floor_structure_map", FLOOR_MAP)
			material.set_shader_parameter("structure_kind", 0)
			material.set_shader_parameter("structure_enabled", 0.0)
		material.set_shader_parameter("base_color_preview", 1.0)

func _restore_base_color_diagnostic() -> void:
	for snapshot: Dictionary in diagnostic_material_snapshots:
		var material := snapshot["material"] as ShaderMaterial
		material.shader = snapshot["shader"] as Shader
		for parameter_name in (snapshot["parameters"] as Dictionary):
			material.set_shader_parameter(parameter_name, (snapshot["parameters"] as Dictionary)[parameter_name])
	diagnostic_material_snapshots.clear()
	for material: ShaderMaterial in baked_receivers:
		if material.shader == STRUCTURE_SHADER:
			material.set_shader_parameter("base_color_preview", 0.0)

func position_structure_review() -> void:
	finish_exit()
	teleport_player(Vector3(3.525, 0.0, -4.75))
	_sync_render_camera()
	_sync_bloom_camera()

func _unhandled_key_input(event: InputEvent) -> void:
	# Consume J here; r3 binds it to an unrelated legacy spill-light experiment.
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_M:
			set_structure_mode((structure_mode + 1) % 4)
			get_viewport().set_input_as_handled()
			return
		if event.physical_keycode == KEY_N:
			set_base_color_mode(not base_color_mode)
			get_viewport().set_input_as_handled()
			return
		if event.physical_keycode == KEY_J:
			position_structure_review()
			get_viewport().set_input_as_handled()
			return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		var labels := ["原材质", "仅墙结构", "仅地面结构", "墙地结构"]
		var diagnostic := " · Base Color检查" if base_color_mode else ""
		info.text = "Room 1 / 局部结构像素 r2 · %s%s\nM切换原/墙/地/两者 · N颜色基线 · J回观察点 · H说明 · WASD移动\n仅左墙和地面各3.2m样段；模型、灯光、布局和r4烘焙不变。" % [labels[structure_mode], diagnostic]
