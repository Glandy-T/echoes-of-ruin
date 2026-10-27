extends "res://scripts/dev/room1_pod_exit_animation_r3.gd"

const SAMPLE_SHADER = preload("res://scripts/dev/room1_surface_sample_r1.gdshader")
const FLOOR_MAP = preload("res://assets/art/room1_surface_sample_r1/floor_sample.png")
const WALL_MAP = preload("res://assets/art/room1_surface_sample_r1/wall_sample.png")
var surface_sample_mode: int = 3
var surface_materials: Dictionary = {}

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	_install_surface_sample("Floor_continuous_no_tile_seams", 1, FLOOR_MAP)
	_install_surface_sample("Wall_left", 2, WALL_MAP)
	set_surface_sample_mode(surface_sample_mode)
	call_deferred("position_surface_review")

func _install_surface_sample(mesh_name: String, kind: int, texture: Texture2D) -> void:
	var receiver := $Shell.find_child(mesh_name, true, false) as MeshInstance3D
	var selected: Array[ShaderMaterial] = []
	for surface in receiver.mesh.get_surface_count():
		var material := receiver.get_active_material(surface) as ShaderMaterial
		if material == null:
			continue
		var source_map := material.get_shader_parameter("color_map") as Texture2D
		# Flat sides/underside stay untouched; target only the existing image face.
		if source_map == null or source_map.get_width() <= 32:
			continue
		# Each receiver already has its own material. Keep that same object in the
		# inherited baked_receivers array so every shadow/light update still applies.
		material.shader = SAMPLE_SHADER
		material.set_shader_parameter("sample_color_map", texture)
		material.set_shader_parameter("sample_kind", kind)
		selected.append(material)
	surface_materials[mesh_name] = selected

func set_surface_sample_mode(mode: int) -> void:
	surface_sample_mode = clampi(mode, 0, 3)
	for key in surface_materials:
		var enabled: bool = (surface_sample_mode == 3 or
			(surface_sample_mode == 1 and key == "Wall_left") or
			(surface_sample_mode == 2 and key == "Floor_continuous_no_tile_seams"))
		for material in surface_materials[key]:
			material.set_shader_parameter("sample_enabled", 1.0 if enabled else 0.0)
	_update_info()

func position_surface_review() -> void:
	finish_exit()
	teleport_player(Vector3(3.525, 0, -4.75))
	_sync_render_camera()
	_sync_bloom_camera()

func _unhandled_key_input(event: InputEvent) -> void:
	super._unhandled_key_input(event)
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode == KEY_M:
			set_surface_sample_mode((surface_sample_mode + 1) % 4)
		elif event.physical_keycode == KEY_J:
			position_surface_review()

func _update_info() -> void:
	if info:
		var labels := ["旧材质", "仅墙样段", "仅地面小片", "墙地小样"]
		info.text = "Room 1 / 局部材料小样 r1 · 待审：%s\nM切换旧/墙/地/两者 · J回样段 · H隐藏说明\nWASD移动；沿用r3镜头、1280×720和原照明\n仅3.2m局部；没有新增墙缝、道路或全室替换。" % labels[surface_sample_mode]
