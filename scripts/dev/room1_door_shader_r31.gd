extends "res://scripts/dev/room1_door_window_r30.gd"

# r31 is deliberately a shader-only door review.  The r30 pixel_map, door
# model, UV, lighting, feedback lamps, animation and the rest of the room stay
# exactly as in r30.  Only DoorPanel's shader is swapped:
#   1 = r30 (v3 door shader), 2 = r31 wall-matched profile + pixel contrast.
const R31_SHADER := preload("res://scripts/dev/room1_door_shader_r31.gdshader")

var r31_mode := 2
var r31_baseline_shader: Shader
var r31_ready := false

func _capture_r30_baseline() -> void:
	super._capture_r30_baseline()
	if r31_ready:
		return
	r31_baseline_shader = panel_material.shader
	assert(r31_baseline_shader != null, "r31 requires r30's door shader as A.")
	r31_ready = true
	set_r31_mode(r31_mode)

func set_r31_mode(requested_mode: int) -> void:
	assert(r31_ready, "r31 shader baseline not initialized")
	r31_mode = clampi(requested_mode, 1, 2)
	# Same material, same r30 pixel_map: only the shader resource changes.
	var pixel_map: Variant = panel_material.get_shader_parameter("pixel_map")
	panel_material.shader = r31_baseline_shader if r31_mode == 1 else R31_SHADER
	panel_material.set_shader_parameter("pixel_map", pixel_map)
	panel_material.set_shader_parameter("strip_on", 1.0 if strip_on else 0.0)
	_update_info()

func get_r31_door_report() -> Dictionary:
	var texture := panel_material.get_shader_parameter("pixel_map") as Texture2D
	return {
		"mode": r31_mode,
		"shader": panel_material.shader.resource_path if panel_material.shader else "",
		"pixel_map": texture.resource_path if texture else "",
		"mutated": ["DoorPanel ShaderMaterial.shader"],
	}

func _update_info() -> void:
	super._update_info()
	if info and r31_ready:
		var label := "A r30（v3门着色器）" if r31_mode == 1 else "B r31（贴墙明暗＋像素对比）"
		info.text = "Room 1 / 主门着色器 r31\n" + label + "；贴图仍是r30，门形、UV、动画、认证灯、绿灯柔光、房间光照与布局不变。1旧／2新。"

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_1, KEY_2]:
		set_r31_mode(1 if event.physical_keycode == KEY_1 else 2)
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)
