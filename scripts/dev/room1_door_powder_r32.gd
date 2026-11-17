extends "res://scripts/dev/room1_door_shader_r31.gd"

# r32: the user fixed the Room 1 door material as M05-L powder-coated steel
# (2026-11-17).  The leaf texture becomes M05-L's native powder-coat grain with
# r30's darker traces, seal ring and status aperture carried over; it is shown
# through the r31 shader with r32-calibrated parameters.  Door model, UV,
# animation, feedback lamps, glow and the rest of the room are unchanged.
#   1 = r30, 2 = r31 (r30 texture + r31 shader), 3 = r32 (M05-L texture + r31 shader)
const R32_DOOR := "res://assets/art/room1_door_powder_r32/door_front.png"
const R31_PARAMS := {
	"leaf_level": 0.19, "contact_floor": 0.62, "contact_height": 0.45,
	"grain_contrast": 2.6, "grain_light_contrast": 1.2,
	"grain_reference": Vector3(0.4735, 0.5271, 0.4508), "fine_contrast": -1.0,
	"fine_edge0": 0.02, "fine_edge1": 0.045,
}
# Calibrated on same-camera captures against the surrounding wall (README).
const R32_PARAMS := {
	"leaf_level": 0.23, "contact_floor": 0.66, "contact_height": 0.45,
	# Revision 2026-11-17: the first r32 (grain 2.0 everywhere) was busier than
	# the wall panels.  Fine powder grain is now softened to 0.5x while painted
	# traces, seal and status aperture keep their native contrast.
	# Second revision (user: take a middle value between the two): fine grain
	# 1.25x, traces/seal/aperture 1.5x -- midway in visible-grain share.
	"grain_contrast": 1.5, "grain_light_contrast": 1.5,
	"fine_contrast": 1.25, "fine_edge0": 0.04, "fine_edge1": 0.09,
	# Median of the r32 texture as the shader actually samples it: sRGB-encoded
	# values under this project's gl_compatibility renderer (verified by sweep).
	"grain_reference": Vector3(0.631, 0.667, 0.635),
}

var r32_mode := 3
var r32_r30_map: Texture2D
var r32_ready := false

func _capture_r30_baseline() -> void:
	super._capture_r30_baseline()
	if r32_ready:
		return
	r32_r30_map = panel_material.get_shader_parameter("pixel_map") as Texture2D
	r32_ready = true
	set_r32_mode(r32_mode)

func _apply_params(params: Dictionary) -> void:
	for key: String in params:
		panel_material.set_shader_parameter(key, params[key])

func set_r32_mode(requested_mode: int) -> void:
	assert(r32_ready, "r32 baseline not initialized")
	r32_mode = clampi(requested_mode, 1, 3)
	panel_material.set_shader_parameter("pixel_map", r32_r30_map)
	set_r31_mode(1 if r32_mode == 1 else 2)
	if r32_mode == 2:
		_apply_params(R31_PARAMS)
	elif r32_mode == 3:
		panel_material.set_shader_parameter("pixel_map", load(R32_DOOR))
		_apply_params(R32_PARAMS)
	_update_info()

func get_r32_door_report() -> Dictionary:
	var texture := panel_material.get_shader_parameter("pixel_map") as Texture2D
	return {
		"mode": r32_mode,
		"shader": panel_material.shader.resource_path if panel_material.shader else "",
		"pixel_map": texture.resource_path if texture else "",
	}

func _update_info() -> void:
	super._update_info()
	if info and r32_ready:
		var labels := {1: "A r30", 2: "B r31（r30贴图＋贴墙着色器）", 3: "C r32（M05-L粉末涂层＋r30痕迹）"}
		info.text = "Room 1 / 主门 r32 粉末涂层\n" + str(labels[r32_mode]) + "；门形、UV、动画、认证灯、绿灯柔光、房间光照与布局不变。1／2／3切换。"

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_1, KEY_2, KEY_3]:
		set_r32_mode({KEY_1: 1, KEY_2: 2, KEY_3: 3}[event.physical_keycode])
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)
