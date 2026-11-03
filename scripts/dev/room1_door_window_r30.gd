extends "res://scripts/dev/room1_door_material_r29.gd"

# r30 is deliberately a texture-only door review.  The r28 room stays intact:
# no model, UV, shader, lighting, feedback or animation properties are changed.
const R30_DOOR := "res://assets/art/room1_door_window_r30/door_front.png"
const R30_SIZE := Vector2i(112, 184)

var r30_mode := 2 # 1 = inherited r29; 2 = same PixelLab body + local Aseprite bezel cleanup.
var r30_baseline_map: Texture2D
var r30_ready := false

func _build_door_glow() -> void:
	# This runs after the complete inherited door has created panel_material.
	super._build_door_glow()
	_capture_r30_baseline()

func _r30_asset_available() -> bool:
	return ResourceLoader.exists(R30_DOOR)

func _capture_r30_baseline() -> void:
	if r30_ready:
		return
	assert(panel_material != null, "r30 requires the inherited integrated-door panel material.")
	r30_baseline_map = panel_material.get_shader_parameter("pixel_map") as Texture2D
	assert(r30_baseline_map != null, "r30 requires r29's existing door pixel_map as A.")
	r30_ready = true
	if _r30_asset_available():
		set_r30_mode(r30_mode)
	else:
		_update_info()

func _restore_r30_pixel_map() -> void:
	# Do not replay a material snapshot: r30 owns exactly this one parameter.
	panel_material.set_shader_parameter("pixel_map", r30_baseline_map)

func set_r30_mode(requested_mode: int) -> void:
	assert(r30_ready, "r30 pixel-map baseline not initialized")
	r30_mode = clampi(requested_mode, 1, 2)
	_restore_r30_pixel_map()
	if r30_mode == 2:
		assert(_r30_asset_available(), "Missing r30 refined door_front.png")
		panel_material.set_shader_parameter("pixel_map", load(R30_DOOR))
	_update_info()

func get_r30_door_runtime_info() -> Dictionary:
	var texture := panel_material.get_shader_parameter("pixel_map") as Texture2D
	var image := texture.get_image() if texture else null
	return {
		"mode": r30_mode,
		"mutated_uniforms": ["pixel_map"],
		"path": texture.resource_path if texture else "",
		"width": texture.get_width() if texture else 0,
		"height": texture.get_height() if texture else 0,
		"decoded_pixel_md5": image.get_data().hex_encode().md5_text() if image else "",
		"baseline_path": r30_baseline_map.resource_path if r30_baseline_map else ""
	}

func get_r30_door_report() -> Dictionary:
	return {"mode": r30_mode, "bindings": 1, "mutated_uniforms": ["pixel_map"], "scope": "integrated DoorPanel pixel_map only"}

func _update_info() -> void:
	super._update_info()
	if info:
		var label := "A r29 白边基线" if r30_mode == 1 else "B r30 认证窗局部精修"
		info.text = "Room 1 / 主门材质 r30\n" + label + "；仅 DoorPanel 的 pixel_map 切换，门形、UV、动画、认证灯、绿灯柔光、房间光照与布局不变。"

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_1, KEY_2]:
		set_r30_mode(1 if event.physical_keycode == KEY_1 else 2)
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)
