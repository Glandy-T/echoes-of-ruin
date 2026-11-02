extends "res://scripts/dev/room1_pod_age_full_r28.gd"

# r29 is deliberately a texture-only door review.  The r28 room stays intact:
# no model, UV, shader, lighting, feedback or animation properties are changed.
const R29_DOOR := "res://assets/art/room1_door_material_r29/door_front.png"
const R29_SIZE := Vector2i(112, 184)

var r29_mode := 2 # 1 = exact inherited r28/v7 map; 2 = r29 PixelLab map.
var r29_baseline_map: Texture2D
var r29_ready := false

func _build_door_glow() -> void:
	# This runs after the complete inherited door has created panel_material.
	super._build_door_glow()
	_capture_r29_baseline()

func _r29_asset_available() -> bool:
	return ResourceLoader.exists(R29_DOOR)

func _capture_r29_baseline() -> void:
	if r29_ready:
		return
	assert(panel_material != null, "r29 requires the inherited integrated-door panel material.")
	r29_baseline_map = panel_material.get_shader_parameter("pixel_map") as Texture2D
	assert(r29_baseline_map != null, "r29 requires r28's existing door pixel_map as A.")
	r29_ready = true
	if _r29_asset_available():
		set_r29_mode(r29_mode)
	else:
		_update_info()

func _restore_r29_pixel_map() -> void:
	# Do not replay a material snapshot: r29 owns exactly this one parameter.
	panel_material.set_shader_parameter("pixel_map", r29_baseline_map)

func set_r29_mode(requested_mode: int) -> void:
	assert(r29_ready, "r29 pixel-map baseline not initialized")
	r29_mode = clampi(requested_mode, 1, 2)
	_restore_r29_pixel_map()
	if r29_mode == 2:
		assert(_r29_asset_available(), "Missing r29 PixelLab door_front.png")
		panel_material.set_shader_parameter("pixel_map", load(R29_DOOR))
	_update_info()

func get_r29_door_runtime_info() -> Dictionary:
	var texture := panel_material.get_shader_parameter("pixel_map") as Texture2D
	var image := texture.get_image() if texture else null
	return {
		"mode": r29_mode,
		"mutated_uniforms": ["pixel_map"],
		"path": texture.resource_path if texture else "",
		"width": texture.get_width() if texture else 0,
		"height": texture.get_height() if texture else 0,
		"decoded_pixel_md5": image.get_data().hex_encode().md5_text() if image else "",
		"baseline_path": r29_baseline_map.resource_path if r29_baseline_map else ""
	}

func get_r29_door_report() -> Dictionary:
	return {"mode": r29_mode, "bindings": 1, "mutated_uniforms": ["pixel_map"], "scope": "integrated DoorPanel pixel_map only"}

func _update_info() -> void:
	super._update_info()
	if info:
		var label := "A r28 / v7 门面基线" if r29_mode == 1 else "B r29 PixelLab 门面候选"
		info.text = "Room 1 / 主门材质 r29\n" + label + "；仅 DoorPanel 的 pixel_map 切换，门形、UV、动画、认证灯、绿灯柔光、房间光照与布局不变。"
