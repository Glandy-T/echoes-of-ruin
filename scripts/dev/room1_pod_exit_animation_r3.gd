@tool
extends "res://scripts/dev/room1_pod_exit_animation_r2.gd"

@export var legacy_lightmap_for_review: bool = false
@export_dir var lightmap_bake_override: String = ""

func _ready() -> void:
	open_hero_bake_root = "res://assets/art/room1_open_hero_bake_r1" if legacy_lightmap_for_review else "res://assets/art/room1_wall_finish_r4"
	if not lightmap_bake_override.is_empty():
		open_hero_bake_root = lightmap_bake_override
	super._ready()
	var uniform_diffuser := false
	var diffuser_scale := 1.0
	var manifest_path := open_hero_bake_root + "/bake_manifest.json"
	if FileAccess.file_exists(manifest_path):
		var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
		uniform_diffuser = bool(manifest.get("uniform_strip_emission",false))
		diffuser_scale = float(manifest.get("diffuser_radiance_scale",1.0))
	for material in baked_receivers:
		material.set_shader_parameter("uniform_strip_emission", 1.0 if uniform_diffuser else 0.0)
		material.set_shader_parameter("diffuser_radiance_scale", diffuser_scale)

func _window_effect_pods() -> PackedStringArray:
	return PackedStringArray(["P02", "P12", "P17"])

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 三亮仓统一玻璃与舱内光 r3\nR重播 · 空格跳过 · 出仓后WASD移动 · G舱光 · H说明\nP12主角仓打开，P02/P17红屏；三仓使用相同透光材质。\n胶囊占位动作预演；像素反光保留，玻璃接缝待后续。"
