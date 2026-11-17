extends "res://scripts/dev/room1_door_light_recess_b1.gd"

## Isolated L1/L2/L3 paper-character review. This scene inherits the frozen
## Room 1 entry unchanged and only swaps the two review Sprite3D textures.
## Candidate PNGs remain outside Godot's import database and are loaded from
## their source paths at runtime, after the art task has supplied them.

const OUT := "res://docs/art/experiments/protagonist_simplification_l123/evidence/game/"
const CORRIDOR_POSITION := Vector3(10.5, 0.05, -4.75)
const LEGACY_VISIBLE_PIXELS := 96.0
const CANDIDATES := [
	{"name": "L1_front", "path": "res://docs/art/experiments/protagonist_simplification_l123/two_tone/L1_front.png"},
	{"name": "L1_side", "path": "res://docs/art/experiments/protagonist_simplification_l123/two_tone/L1_side.png"},
	{"name": "L2_front", "path": "res://docs/art/experiments/protagonist_simplification_l123/two_tone/L2_front.png"},
	{"name": "L2_side", "path": "res://docs/art/experiments/protagonist_simplification_l123/two_tone/L2_side.png"},
	{"name": "L3_front", "path": "res://docs/art/experiments/protagonist_simplification_l123/two_tone/L3_front.png"},
	{"name": "L3_side", "path": "res://docs/art/experiments/protagonist_simplification_l123/two_tone/L3_side.png"},
]

var _legacy_states: Dictionary = {}
var _legacy_visible_height_m := 0.0
var _active_mode := 0
var _capture_requested := false
var _prepared := false


func _ready() -> void:
	# The frozen Room 1 entry creates the actual game cameras, material, bloom,
	# door state, and scene composition before this review freezes them.
	super._ready()
	if Engine.is_editor_hint():
		return
	_capture_requested = OS.get_cmdline_user_args().has("--capture")
	call_deferred("_prepare_review")


func _prepare_review() -> void:
	if not is_instance_valid(paper_hero) or not is_instance_valid(bloom_paper_hero):
		push_error("L1/L2/L3 review needs the inherited paper_hero sprites.")
		return
	_snapshot_legacy_state()
	if _legacy_visible_height_m <= 0.0:
		push_error("L1/L2/L3 review could not determine inherited paper height.")
		return
	# The comparison is explicitly full-resolution 1280x720. This controls the
	# existing pixel presentation, not a separate technical review camera.
	set_pixel_mode(0)
	finish_exit()
	if review_ui:
		review_ui.close_dialogue()
	_freeze_dynamic_screens()
	# One original follow-camera calculation at the fixed gameplay location.
	teleport_player(CORRIDOR_POSITION)
	var camera := get_node_or_null("ReviewCamera") as Camera3D
	if camera == null:
		push_error("L1/L2/L3 review requires the inherited ReviewCamera.")
		return
	camera.fov = 50.0
	_sync_render_camera()
	_sync_bloom_camera()
	# Prevent the inherited idle/walk driver, pod UI, and door input from changing
	# the static side-by-side appearance after the one camera placement above.
	set_process(false)
	set_physics_process(false)
	_prepared = true
	_set_mode(0)
	if _capture_requested:
		call_deferred("_capture_all")


func _snapshot_legacy_state() -> void:
	for sprite: Sprite3D in [paper_hero, bloom_paper_hero]:
		_legacy_states[sprite.get_instance_id()] = {
			"texture": sprite.texture,
			"hframes": sprite.hframes,
			"vframes": sprite.vframes,
			"frame": sprite.frame,
			"pixel_size": sprite.pixel_size,
			"local_y": sprite.position.y,
		}
	# This is deliberately read from the inherited review sprite rather than
	# assuming 1.65m: current Room 1 is the only size authority for this check.
	_legacy_visible_height_m = paper_hero.pixel_size * LEGACY_VISIBLE_PIXELS


func _freeze_dynamic_screens() -> void:
	for pod: Node3D in room_pods.values():
		var viewport := pod.get("_screen_viewport") as SubViewport
		if viewport:
			viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED


func _candidate(mode: int) -> Dictionary:
	if mode < 0 or mode >= CANDIDATES.size():
		return {}
	return CANDIDATES[mode]


func _load_candidate(mode: int) -> Texture2D:
	var candidate := _candidate(mode)
	if candidate.is_empty():
		return null
	var path: String = candidate["path"]
	if not FileAccess.file_exists(path):
		return null
	var image := Image.load_from_file(ProjectSettings.globalize_path(path))
	if image == null or image.is_empty():
		return null
	var texture := ImageTexture.create_from_image(image)
	texture.set_meta("review_source_path", path)
	return texture


func _alpha_bbox(texture: Texture2D) -> Rect2i:
	if texture == null:
		return Rect2i()
	var image := texture.get_image()
	if image == null:
		return Rect2i()
	var extent := Rect2i(Vector2i.ZERO, image.get_size())
	var left := extent.end.x
	var top := extent.end.y
	var right := extent.position.x - 1
	var bottom := extent.position.y - 1
	for y in range(extent.position.y, extent.end.y):
		for x in range(extent.position.x, extent.end.x):
			if image.get_pixel(x, y).a > 0.0:
				left = mini(left, x)
				top = mini(top, y)
				right = maxi(right, x)
				bottom = maxi(bottom, y)
	if right < left or bottom < top:
		return Rect2i()
	return Rect2i(left, top, right - left + 1, bottom - top + 1)


func _set_mode(mode: int) -> void:
	if not _prepared:
		return
	var texture := _load_candidate(mode)
	if texture == null:
		var missing := _candidate(mode)
		push_warning("L1/L2/L3 review candidate is not available: " + str(missing.get("path", "invalid mode")))
		return
	if texture.get_width() != 128 or texture.get_height() != 128:
		push_error("L1/L2/L3 candidate must be 128x128: " + str(texture.get_meta("review_source_path", "")))
		return
	var bbox := _alpha_bbox(texture)
	if bbox.size.y <= 0:
		push_error("L1/L2/L3 candidate has no visible alpha pixels.")
		return
	# The entire square image retains its native aspect ratio. Scaling uses only
	# alpha-visible height; the local offset locks alpha's sole to player y = 0.
	for sprite: Sprite3D in [paper_hero, bloom_paper_hero]:
		sprite.texture = texture
		sprite.hframes = 1
		sprite.vframes = 1
		sprite.frame = 0
		sprite.pixel_size = _legacy_visible_height_m / float(bbox.size.y)
		sprite.position.y = (float(bbox.end.y) - float(texture.get_height()) * 0.5) * sprite.pixel_size
	_sync_paper_hero()
	_sync_paper_lighting()
	_active_mode = mode
	_update_review_info()


func _current_metrics() -> Dictionary:
	var texture := paper_hero.texture as Texture2D
	var bbox := _alpha_bbox(texture)
	var visible_height := paper_hero.pixel_size * float(bbox.size.y)
	var candidate := _candidate(_active_mode)
	return {
		"mode": candidate.get("name", "unset"),
		"source": texture.get_meta("review_source_path", texture.resource_path),
		"native_image_px": [texture.get_width(), texture.get_height()],
		"alpha_bbox_px": {"x": bbox.position.x, "y": bbox.position.y, "width": bbox.size.x, "height": bbox.size.y},
		"foot_row_px_exclusive": bbox.end.y,
		"world_visible_height_m": visible_height,
		"native_pixels_per_m": float(bbox.size.y) / visible_height if visible_height > 0.0 else 0.0,
		"sprite_pixel_size": paper_hero.pixel_size,
		"local_y": paper_hero.position.y,
		"sprite_shaded_flag": paper_hero.get_draw_flag(SpriteBase3D.FLAG_SHADED),
		"texture_filter": paper_hero.texture_filter,
		"billboard": paper_hero.billboard,
		"cast_shadow": paper_hero.cast_shadow,
		"material_override_shader": paper_light_material.shader.resource_path if paper_light_material else "",
		"lighting_boundary": "Inherited paper Sprite3D strip-light approximation and existing bloom copy only; no final mesh, bones, skinning, GI receiver, or final 3D material is evaluated.",
	}


func _update_review_info() -> void:
	if not info or not _prepared:
		return
	var metric := _current_metrics()
	info.text = "Room 1 / 主角简化程度审图 · 非正式角色\n1 L1正 · 2 L1侧 · 3 L2正 · 4 L2侧 · 5 L3正 · 6 L3侧 · H隐藏说明\n%s · 可见高 %.3fm · %.1f 原生px/m · 固定游戏镜头50°" % [metric["mode"], metric["world_visible_height_m"], metric["native_pixels_per_m"]]


func _unhandled_key_input(event: InputEvent) -> void:
	if not _prepared or not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.physical_keycode >= KEY_1 and event.physical_keycode <= KEY_6:
		_set_mode(event.physical_keycode - KEY_1)
		get_viewport().set_input_as_handled()
		return
	if event.physical_keycode == KEY_H:
		if info and info.get_parent():
			info.get_parent().visible = not info.get_parent().visible
		get_viewport().set_input_as_handled()


func _frames(count: int) -> void:
	for _i in count:
		await get_tree().process_frame


func _camera_record(camera: Camera3D) -> Dictionary:
	var actual := render_viewport.get_camera_3d() if render_viewport else null
	return {
		"review_camera_transform": str(camera.global_transform),
		"render_camera_transform": str(actual.global_transform) if actual else "",
		"render_camera_matches_review": actual.global_transform.is_equal_approx(camera.global_transform) if actual else false,
		"fov": camera.fov,
		"output_viewport": [get_viewport().get_texture().get_width(), get_viewport().get_texture().get_height()],
		"internal_viewport": [render_viewport.size.x, render_viewport.size.y] if render_viewport else [],
		"player_position": str(player.global_position),
	}


func _capture_all() -> void:
	var missing: Array[String] = []
	for mode in CANDIDATES.size():
		if _load_candidate(mode) == null:
			missing.append(str(CANDIDATES[mode]["path"]))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	if not missing.is_empty():
		var pending := FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE)
		pending.store_string(JSON.stringify({"status": "waiting_for_candidate_png", "required": missing}, "\t"))
		pending.close()
		push_warning("L1/L2/L3 capture waits for supplied two-tone PNGs; no fallback capture was created.")
		get_tree().quit()
		return
	if info and info.get_parent():
		info.get_parent().hide()
	var camera := get_node_or_null("ReviewCamera") as Camera3D
	assert(camera != null, "L1/L2/L3 review requires ReviewCamera.")
	var records: Array[Dictionary] = []
	for mode in CANDIDATES.size():
		_set_mode(mode)
		# Camera placement is frozen; these only copy it to the real render paths.
		_sync_render_camera()
		_sync_bloom_camera()
		await _frames(12)
		await RenderingServer.frame_post_draw
		var image := get_viewport().get_texture().get_image()
		assert(image.get_width() == 1280 and image.get_height() == 720, "Capture must be 1280x720.")
		var name: String = CANDIDATES[mode]["name"]
		var filename := "game_%s.png" % name
		assert(image.save_png(OUT + filename) == OK)
		var record := _camera_record(camera)
		record["file"] = filename
		record["appearance"] = _current_metrics()
		records.append(record)
		print("PROTAGONIST_SIMPLIFICATION_SHOT ", filename)
	var report := {
		"status": "captured",
		"capture_contract": "Frozen Room 1 gameplay presentation. Player teleported once to the fixed corridor position, inherited follow camera evaluated once, FOV fixed at 50, then six texture-only modes captured without camera recalculation.",
		"baseline_visible_height_m": _legacy_visible_height_m,
		"baseline_formula": "inherited paper_hero.pixel_size * 96",
		"review_camera": "ReviewCamera",
		"shots": records,
	}
	var record_file := FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE)
	record_file.store_string(JSON.stringify(report, "\t"))
	record_file.close()
	get_tree().quit()
