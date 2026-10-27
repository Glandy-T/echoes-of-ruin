@tool
extends "res://scripts/dev/room1_sprite_player_review_r1.gd"

## Dynamic paper sprites cannot receive the room's static lightmap. This is a
## small, position-aware approximation of the already established ribbon lights.
const PAPER_LIGHT_SHADER := preload("res://scripts/dev/room1_sprite_player_strip_lighting_r2.gdshader")

var paper_light_material: ShaderMaterial

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint() or not is_instance_valid(paper_hero):
		return
	paper_light_material = ShaderMaterial.new()
	paper_light_material.shader = PAPER_LIGHT_SHADER
	paper_hero.material_override = paper_light_material
	_sync_paper_lighting()

func _process(delta: float) -> void:
	super._process(delta)
	_sync_paper_lighting()

func _sync_paper_lighting() -> void:
	if not is_instance_valid(paper_hero) or not paper_light_material:
		return
	paper_light_material.set_shader_parameter("paper_texture", paper_hero.texture)
	paper_light_material.set_shader_parameter("strip_on", 1.0 if strip_on else 0.0)

func paper_light_level_at(point: Vector3) -> float:
	var ribbon := 0.0
	for index in 8:
		var x := lerpf(0.205, 20.795, (float(index) + 0.5) / 8.0)
		var front := Vector3(x, 3.05, -0.205) - point
		var rear := Vector3(x, 3.05, -9.295) - point
		ribbon += 1.0 / (1.0 + 0.18 * front.length_squared())
		ribbon += 1.0 / (1.0 + 0.18 * rear.length_squared())
	return 0.10 + (0.13 + 0.38 * clamp(ribbon * 0.5, 0.0, 1.0)) * (1.0 if strip_on else 0.0)

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 2D纸片主角受光 r2 · 待审\nWASD移动 · R复位 · L墙灯 · O开/关盖 · G内侧灯管 · B屏幕\n角色以1.65m纸片进入3D空间；受光近似沿用连续灯带位置，非动态GI。"
