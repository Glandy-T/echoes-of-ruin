extends "res://scripts/dev/room1_pod_exit_animation_r3.gd"

const FULL_SHADER = preload("res://scripts/dev/room1_surface_full_room_r1.gdshader")
const FLOOR_MAP = preload("res://assets/art/room1_surface_sample_r1/floor_sample.png")
const WALL_MAP = preload("res://assets/art/room1_surface_sample_r1/wall_sample.png")
@export_range(0.0,1.0) var wall_material_strength := 0.5
@export_range(0.0,1.0) var floor_material_strength := 0.6
var full_surface_mode: int = 3
var full_surface_materials: Dictionary = {}

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	_install_full_surface("Floor_continuous_no_tile_seams",1)
	for wall in ["Wall_front","Wall_left","Wall_right","Wall_rear_left","Wall_rear_right","Wall_rear_door_header"]:
		_install_full_surface(wall,2)
	set_full_surface_mode(full_surface_mode)
	call_deferred("position_material_review")

func _install_full_surface(name: String, kind: int) -> void:
	var mesh := $Shell.find_child(name,true,false) as MeshInstance3D
	var materials: Array[ShaderMaterial] = []
	for surface in mesh.mesh.get_surface_count():
		var material := mesh.get_active_material(surface) as ShaderMaterial
		var texture := material.get_shader_parameter("color_map") as Texture2D
		if texture == null or texture.get_width() <= 32:
			continue
		material.shader = FULL_SHADER
		material.set_shader_parameter("floor_material_map",FLOOR_MAP)
		material.set_shader_parameter("wall_material_map",WALL_MAP)
		material.set_shader_parameter("full_surface_kind",kind)
		material.set_shader_parameter("material_center", Color("#5A6C73") if kind == 1 else Color("#D3D6C9"))
		material.set_shader_parameter("material_strength",floor_material_strength if kind == 1 else wall_material_strength)
		materials.append(material)
	full_surface_materials[name] = materials

func set_full_surface_mode(mode: int) -> void:
	full_surface_mode = clampi(mode,0,3)
	for name in full_surface_materials:
		var enabled: bool = full_surface_mode == 3 or (full_surface_mode == 1 and name != "Floor_continuous_no_tile_seams") or (full_surface_mode == 2 and name == "Floor_continuous_no_tile_seams")
		for material in full_surface_materials[name]:
			material.set_shader_parameter("full_surface_enabled",1.0 if enabled else 0.0)
	_update_info()

func position_material_review() -> void:
	finish_exit()
	teleport_player(Vector3(3.525,0,-4.75))
	_sync_render_camera()
	_sync_bloom_camera()

func _unhandled_key_input(event: InputEvent) -> void:
	# J already controls a legacy spill-light comparison in the ancestor scene.
	# Consume candidate review keys here so returning to the view cannot change lighting.
	if event is InputEventKey and event.physical_keycode in [KEY_M,KEY_J]:
		if event.pressed and not event.echo:
			if event.physical_keycode == KEY_M:
				set_full_surface_mode((full_surface_mode+1)%4)
			else:
				position_material_review()
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		var labels := ["原材质","整室墙面","整块地面","整室墙地"]
		info.text = "Room 1 / 整室材质候选 r1 · %s\nM切换原/墙/地/两者 · J观察点 · H说明 · WASD移动" % labels[full_surface_mode]
