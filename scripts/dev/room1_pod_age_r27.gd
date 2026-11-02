extends "res://scripts/dev/room1_floor_detail_full_r26.gd"

# r27 is a deliberately narrow review: only P12's three opaque exterior
# colour maps may change.  All state captured here is from the already-loaded
# r26 scene, so A is the actual current room presentation rather than a
# reconstructed approximation.
const R27_ROOT := "res://assets/art/room1_pod_age_r27/"
const R27_MAPS := {
	"lid": "lid.png",
	"shell_side": "shell_side.png",
	"shell_end": "shell_end.png",
}
const R27_EXPECTED_SIZES := {
	"lid": Vector2i(96, 184),
	"shell_side": Vector2i(184, 56),
	"shell_end": Vector2i(96, 56),
}

var r27_mode := 1 # 1 = current r26 P12 exterior; 2 = r27 PixelLab candidate.
var r27_p12_snapshots: Array[Dictionary] = []
var r27_ready := false

func _build_door_glow() -> void:
	super._build_door_glow()
	_capture_r27_p12_baseline()

func _capture_r27_p12_baseline() -> void:
	if r27_ready:
		return
	assert(room_pod_finishes.has("P12"), "r27 requires the r19 P12 finish registry.")
	for entry: Dictionary in (room_pod_finishes["P12"] as RefCounted).entries:
		var role := str(entry.role)
		if not R27_MAPS.has(role):
			continue
		var material := entry.material as ShaderMaterial
		# The r27 contract owns only this one binding.  In particular, do not
		# snapshot/replay pose, irradiance, screen, glass, shadow or GI uniforms.
		r27_p12_snapshots.append({
			"role": role,
			"material": material,
			"color_map": material.get_shader_parameter("color_map"),
		})
	assert(not r27_p12_snapshots.is_empty(), "r27 found no P12 exterior materials.")
	r27_ready = true
	if _r27_assets_available():
		set_r27_mode(r27_mode)
	else:
		_update_info()

func _r27_assets_available() -> bool:
	if r27_p12_snapshots.is_empty():
		return false
	for file_name: String in R27_MAPS.values():
		if not ResourceLoader.exists(R27_ROOT + file_name):
			return false
	return true

func _restore_r27_p12_maps() -> void:
	for item: Dictionary in r27_p12_snapshots:
		(item.material as ShaderMaterial).set_shader_parameter("color_map", item.color_map)

func set_r27_mode(requested_mode: int) -> void:
	assert(r27_ready, "r27 P12 baseline not initialized")
	r27_mode = clampi(requested_mode, 1, 2)
	_restore_r27_p12_maps()
	if r27_mode == 2:
		assert(_r27_assets_available(), "Missing one or more r27 P12 exterior maps.")
		for item: Dictionary in r27_p12_snapshots:
			var role := str(item.role)
			(item.material as ShaderMaterial).set_shader_parameter("color_map", load(R27_ROOT + str(R27_MAPS[role])))
	_update_info()

func get_pod_age_r27_report() -> Dictionary:
	var maps: Dictionary = {}
	for item: Dictionary in r27_p12_snapshots:
		var texture := (item.material as ShaderMaterial).get_shader_parameter("color_map") as Texture2D
		maps[str(item.role)] = texture.resource_path if texture else ""
	return {
		"mode": r27_mode,
		"p12_exterior_maps": maps,
		"mutated_uniforms": ["color_map"],
		"scope": "P12 lid, shell_side and shell_end only",
	}

func get_r27_runtime_map_info() -> Dictionary:
	# This reads the imported Texture2D actually bound by the live scene, rather
	# than trusting the source PNG's filesystem metadata.  It makes stale import
	# cache failures visible in both the verifier and captured review record.
	var maps: Dictionary = {}
	for item: Dictionary in r27_p12_snapshots:
		var texture := (item.material as ShaderMaterial).get_shader_parameter("color_map") as Texture2D
		var image := texture.get_image() if texture else null
		maps[str(item.role)] = {
			"path": texture.resource_path if texture else "",
			"width": texture.get_width() if texture else 0,
			"height": texture.get_height() if texture else 0,
			"decoded_pixel_md5": image.get_data().hex_encode().md5_text() if image else "",
		}
	return maps

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():
		return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1: set_r27_mode(1)
			KEY_2: set_r27_mode(2)
			KEY_O: standard.toggle()
			KEY_H: info.get_parent().visible = not info.get_parent().visible
			_:
				super._unhandled_key_input(event)
				return
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if not info:
		return
	var label := "A r26 当前 P12 外壳" if r27_mode == 1 else "B r27 PixelLab 做旧候选"
	info.text = "Room 1 / P12 做旧贴图 r27\n" + label + "；仅切换 lid、shell_side、shell_end 三张颜色图，UV、模型、灯、GI、玻璃、屏幕、编号、开闭与其余19舱不变\n1 当前材质 · 2 r27候选 · O开盖 · H说明"
