extends "res://scripts/dev/room1_pod_age_r27.gd"

# r28 promotes the accepted r27 P12 finish to a controlled full-room review.
# It owns exactly sixty exterior color-map bindings: 20 pods x lid/side/end.
const R28_ROOT := "res://assets/art/room1_pod_age_full_r28/"
const R28_LAYOUT := R28_ROOT + "layout_variants.json"
const R28_ROLES := ["lid", "shell_side", "shell_end"]
const R28_SIZES := {"lid": Vector2i(96, 184), "shell_side": Vector2i(184, 56), "shell_end": Vector2i(96, 56)}

var r28_mode := 2 # 1 = accepted r27 baseline; 2 = full-room r28 assignment.
var r28_layout: Dictionary = {}
var r28_snapshots: Array[Dictionary] = []
var r28_ready := false

func _build_door_glow() -> void:
	# r27 captures r26 first.  Deliberately promote P12 to the accepted r27 maps
	# before this child records its A baseline; never replay the old r26 P12 maps.
	super._build_door_glow()
	_capture_r28_baseline()

func _load_r28_layout() -> bool:
	if not r28_layout.is_empty():
		return true
	if not FileAccess.file_exists(R28_LAYOUT):
		return false
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(R28_LAYOUT))
	if not (parsed is Dictionary) or not (parsed as Dictionary).has("pods"):
		return false
	r28_layout = parsed as Dictionary
	return true

func _layout_entries() -> Array:
	return r28_layout.get("pods", []) as Array

func _entry_for_pod(id: String) -> Dictionary:
	for item in _layout_entries():
		if item is Dictionary and str((item as Dictionary).get("id", "")) == id:
			return item as Dictionary
	return {}

func _path_for(id: String, role: String) -> String:
	var item := _entry_for_pod(id)
	var maps: Dictionary = item.get("maps", {})
	return str(maps.get(role, ""))

func _r28_assets_available() -> bool:
	if not _load_r28_layout() or _layout_entries().size() != 20:
		return false
	var ids := {}
	for item in _layout_entries():
		if not item is Dictionary:
			return false
		var id := str((item as Dictionary).get("id", ""))
		var number := int((item as Dictionary).get("number", 0))
		if id.is_empty() or number < 1 or number > 20 or ids.has(id):
			return false
		ids[id] = true
		for role: String in R28_ROLES:
			var path := _path_for(id, role)
			if path.is_empty() or not ResourceLoader.exists(path):
				return false
	return true

func _capture_r28_baseline() -> void:
	if r28_ready:
		return
	assert(r27_ready, "r28 requires r27 to capture its original r26 bindings first.")
	assert(_r27_assets_available(), "r28 needs the accepted r27 P12 maps for its A baseline.")
	set_r27_mode(2)
	for id: String in room_pod_finishes:
		for entry: Dictionary in (room_pod_finishes[id] as RefCounted).entries:
			var role := str(entry.role)
			if not R28_ROLES.has(role):
				continue
			var material := entry.material as ShaderMaterial
			r28_snapshots.append({"id": id, "role": role, "material": material, "color_map": material.get_shader_parameter("color_map")})
	assert(r28_snapshots.size() == 60, "r28 must capture exactly 60 exterior color-map bindings.")
	var accepted := false
	for item: Dictionary in r28_snapshots:
		if str(item.id) == "P12" and str(item.role) == "lid":
			accepted = str((item.color_map as Texture2D).resource_path).begins_with(R27_ROOT)
	assert(accepted, "r28 A must retain r27's accepted P12 finish.")
	r28_ready = true
	if _r28_assets_available():
		set_r28_mode(r28_mode)
	else:
		_update_info()

func _restore_r28_maps() -> void:
	for item: Dictionary in r28_snapshots:
		(item.material as ShaderMaterial).set_shader_parameter("color_map", item.color_map)

func set_r28_mode(requested_mode: int) -> void:
	assert(r28_ready, "r28 baseline not initialized")
	r28_mode = clampi(requested_mode, 1, 2)
	_restore_r28_maps()
	if r28_mode == 2:
		assert(_r28_assets_available(), "Missing r28 layout or one of its 60 imported exterior maps.")
		for item: Dictionary in r28_snapshots:
			var path := _path_for(str(item.id), str(item.role))
			(item.material as ShaderMaterial).set_shader_parameter("color_map", load(path))
	_update_info()

func get_r28_runtime_map_info() -> Dictionary:
	var maps: Dictionary = {}
	for item: Dictionary in r28_snapshots:
		var texture := (item.material as ShaderMaterial).get_shader_parameter("color_map") as Texture2D
		var image := texture.get_image() if texture else null
		maps[str(item.id) + "/" + str(item.role)] = {"path": texture.resource_path if texture else "", "width": texture.get_width() if texture else 0, "height": texture.get_height() if texture else 0, "decoded_pixel_md5": image.get_data().hex_encode().md5_text() if image else ""}
	return maps

func get_pod_age_r28_report() -> Dictionary:
	return {"mode": r28_mode, "bindings": r28_snapshots.size(), "mutated_uniforms": ["color_map"], "scope": "all 20 pods, exterior lid/shell_side/shell_end only"}

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():
		return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1: set_r28_mode(1)
			KEY_2: set_r28_mode(2)
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
	var label := "A 已认可 r27 / P12 基线" if r28_mode == 1 else "B r28 全20舱差分"
	info.text = "Room 1 / 全舱做旧 r28\n" + label + "；仅切换20舱的 lid、shell_side、shell_end 共60个 color_map，模型、UV、布局、灯、GI、玻璃、屏幕、编号、开闭不变\n1 基线 · 2 全舱候选 · O开盖 · H说明"
