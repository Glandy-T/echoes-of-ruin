extends "res://scripts/dev/room1_door_window_r30.gd"

## Isolated Room 1 paper-character review.  It inherits the committed r30 room
## unchanged and never writes its camera, door, pod, or formal-scene resources.
## The candidate PNGs are intentionally loaded at runtime: v3 is produced by
## PixelLab outside Godot and may not exist while this review scene is checked in.

const V2_PATH := "res://docs/art/experiments/protagonist_legacy_refine_v3/source/adult_v2_original.png"
const V3_PATH := "res://docs/art/experiments/protagonist_legacy_refine_v3/front_candidate.png"
const OUT := "res://docs/art/experiments/protagonist_legacy_refine_v3/evidence/game/"
const LEGACY_FRAME_WIDTH := 96
const CAPTURE_VIEWS := [
	{"name": "front_left", "position": Vector3(3.0, 0.05, -3.8)},
	{"name": "front_middle", "position": Vector3(10.5, 0.05, -4.75)},
	{"name": "front_right", "position": Vector3(14.8, 0.05, -3.8)},
]

var _legacy_states: Dictionary = {}
var _legacy_bbox := Rect2i()
var _legacy_visible_height_m := 0.0
var _active_mode := 1
var _active_view := 0
var _capture_requested := false
var _prepared := false


func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	_capture_requested = OS.get_cmdline_user_args().has("--capture")
	call_deferred("_prepare_review")


func _prepare_review() -> void:
	if not is_instance_valid(paper_hero) or not is_instance_valid(bloom_paper_hero):
		push_error("Protagonist context v3 needs the inherited paper_hero sprites.")
		return
	_snapshot_legacy_state()
	finish_exit()
	if review_ui:
		review_ui.close_dialogue()
	_freeze_dynamic_screens()
	# This is a static appearance review.  In particular, do not let the
	# inherited idle/walk driver replace candidate textures or advance frames.
	set_process(false)
	set_physics_process(false)
	_prepared = true
	_set_view(0)
	_set_mode(1)
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
	_legacy_bbox = _alpha_bbox(paper_hero.texture, Rect2i(0, 0, LEGACY_FRAME_WIDTH, paper_hero.texture.get_height()))
	if _legacy_bbox.size.y <= 0:
		push_error("Legacy idle frame has no readable alpha bounds.")
		return
	# Do not assume a character height.  The inherited r1 default is the source
	# of truth (normally 1.4025 m): its stated 96 visible legacy pixels define it.
	# The alpha result remains recorded below as an independent runtime check.
	_legacy_visible_height_m = paper_hero.pixel_size * 96.0


func _freeze_dynamic_screens() -> void:
	for pod: Node3D in room_pods.values():
		var viewport := pod.get("_screen_viewport") as SubViewport
		if viewport:
			viewport.render_target_update_mode = SubViewport.UPDATE_DISABLED


func _texture_for_mode(mode: int) -> Texture2D:
	match mode:
		1:
			var state: Dictionary = _legacy_states[paper_hero.get_instance_id()]
			return state["texture"] as Texture2D
		2:
			return _load_candidate(V2_PATH)
		3, 4:
			return _load_candidate(V3_PATH)
	return null


func _load_candidate(path: String) -> Texture2D:
	# docs/art is excluded from Godot's import scan. Load the review-only PNG
	# directly, without changing that exclusion or adding production assets.
	if not FileAccess.file_exists(path):
		return null
	var image := Image.load_from_file(ProjectSettings.globalize_path(path))
	if image == null or image.is_empty():
		return null
	var texture := ImageTexture.create_from_image(image)
	texture.set_meta("review_source_path", path)
	return texture


func _set_mode(mode: int) -> void:
	if not _prepared:
		return
	var texture := _texture_for_mode(mode)
	if texture == null:
		push_warning("Candidate texture is not available yet: " + (V3_PATH if mode >= 3 else V2_PATH))
		return
	var bbox := _alpha_bbox(texture, Rect2i(0, 0, texture.get_width(), texture.get_height()))
	if bbox.size.y <= 0:
		push_error("Candidate has no alpha-visible pixels: " + texture.resource_path)
		return
	var visible_height := _legacy_visible_height_m * (0.95 if mode == 4 else 1.0)
	for sprite: Sprite3D in [paper_hero, bloom_paper_hero]:
		if mode == 1:
			var state: Dictionary = _legacy_states[sprite.get_instance_id()]
			sprite.texture = state["texture"]
			sprite.hframes = state["hframes"]
			sprite.vframes = state["vframes"]
			sprite.frame = 0
			sprite.pixel_size = state["pixel_size"]
			sprite.position.y = state["local_y"]
		else:
			sprite.texture = texture
			sprite.hframes = 1
			sprite.vframes = 1
			sprite.frame = 0
			sprite.pixel_size = visible_height / float(bbox.size.y)
			# Sprite3D is centred on the whole texture.  Alpha's exclusive end row
			# is the visible sole, so this locks every candidate to player y = 0.
			sprite.position.y = (float(bbox.end.y) - float(texture.get_height()) * 0.5) * sprite.pixel_size
	_sync_paper_hero()
	_sync_paper_lighting()
	_active_mode = mode
	_update_review_info()


func _set_view(index: int) -> void:
	if not _prepared:
		return
	_active_view = posmod(index, CAPTURE_VIEWS.size())
	# teleport_player is the original Room 1 path and invokes update_follow_camera
	# once.  Candidate swaps below never invoke it, keeping the four-mode matrix
	# identical at each game view.
	teleport_player(CAPTURE_VIEWS[_active_view].position)
	var camera := get_node_or_null("ReviewCamera") as Camera3D
	if camera:
		camera.fov = 50.0
	_sync_render_camera()
	_sync_bloom_camera()
	_update_review_info()


func _alpha_bbox(texture: Texture2D, region: Rect2i) -> Rect2i:
	if texture == null:
		return Rect2i()
	var image := texture.get_image()
	if image == null:
		return Rect2i()
	var bounded := region.intersection(Rect2i(Vector2i.ZERO, image.get_size()))
	var left := bounded.end.x
	var top := bounded.end.y
	var right := bounded.position.x - 1
	var bottom := bounded.position.y - 1
	for y in range(bounded.position.y, bounded.end.y):
		for x in range(bounded.position.x, bounded.end.x):
			if image.get_pixel(x, y).a > 0.0:
				left = mini(left, x)
				top = mini(top, y)
				right = maxi(right, x)
				bottom = maxi(bottom, y)
	if right < left or bottom < top:
		return Rect2i()
	return Rect2i(left, top, right - left + 1, bottom - top + 1)


func _review_mode_name(mode: int) -> String:
	return ["legacy idle #0", "v2 PixelLab", "v3 PixelLab", "v3 PixelLab short 95%"][mode - 1]


func _current_metrics() -> Dictionary:
	var texture := paper_hero.texture as Texture2D
	var region := Rect2i(0, 0, texture.get_width() / maxi(paper_hero.hframes, 1), texture.get_height() / maxi(paper_hero.vframes, 1))
	var bbox := _alpha_bbox(texture, region)
	var visible_height := paper_hero.pixel_size * float(bbox.size.y)
	return {
		"mode": _review_mode_name(_active_mode),
		"source": texture.get_meta("review_source_path", texture.resource_path),
		"alpha_bbox_px": {"x": bbox.position.x, "y": bbox.position.y, "width": bbox.size.x, "height": bbox.size.y},
		"foot_row_px": bbox.end.y,
		"world_visible_height_m": visible_height,
		"native_pixels_per_m": float(bbox.size.y) / visible_height if visible_height > 0.0 else 0.0,
		"sprite_pixel_size": paper_hero.pixel_size,
		"local_y": paper_hero.position.y,
		"sprite_shaded_flag": paper_hero.get_draw_flag(SpriteBase3D.FLAG_SHADED),
		"lighting_mode": "Inherited custom unshaded strip-light approximation",
		"material_override_shader": paper_light_material.shader.resource_path if paper_light_material else "",
		"texture_filter": paper_hero.texture_filter,
		"billboard": paper_hero.billboard,
		"cast_shadow": paper_hero.cast_shadow,
		"projected_sole": str(render_camera.unproject_position(player.global_position)),
		"projected_crown": str(render_camera.unproject_position(player.global_position + Vector3(0, visible_height, 0))),
		"nonfinal_3d_lighting_boundary": "Paper Sprite3D only; no final mesh, bones, skinning, GI receiver, or final 3D material is being approved. The inherited paper strip-light shader is a local approximation, and bloom is the existing secondary render copy.",
	}


func _update_review_info() -> void:
	if not info or not _prepared:
		return
	var metric := _current_metrics()
	info.text = "Room 1 / 主角纸片比例对照 v3 · 审图专用\n1 legacy · 2 v2 · 3 v3 · 4 v3短95%% · ,/. 切换机位 · H隐藏说明\n%s · 机位 %s · 可见高 %.3fm · %.1f 原生px/m\n固定 Room 1 游戏镜头/光照；非最终3D受光。" % [_review_mode_name(_active_mode), CAPTURE_VIEWS[_active_view]["name"], metric["world_visible_height_m"], metric["native_pixels_per_m"]]


func _unhandled_key_input(event: InputEvent) -> void:
	if not _prepared or not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_1, KEY_2, KEY_3, KEY_4:
			_set_mode(event.physical_keycode - KEY_1 + 1)
			get_viewport().set_input_as_handled()
		KEY_COMMA:
			_set_view(_active_view - 1)
			get_viewport().set_input_as_handled()
		KEY_PERIOD:
			_set_view(_active_view + 1)
			get_viewport().set_input_as_handled()
		KEY_H:
			if info and info.get_parent():
				info.get_parent().visible = not info.get_parent().visible
			get_viewport().set_input_as_handled()
		_:
			pass


func _frames(count: int) -> void:
	for _index in count:
		await get_tree().process_frame


func _capture_all() -> void:
	# v3 is supplied later by PixelLab.  A missing future asset is a pending input,
	# not an invitation to capture a fallback or change the established workflow.
	if _load_candidate(V2_PATH) == null or _load_candidate(V3_PATH) == null:
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
		var pending := FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE)
		pending.store_string(JSON.stringify({"status": "waiting_for_candidate_png", "required": [V2_PATH, V3_PATH]}, "\t"))
		pending.close()
		push_warning("Protagonist v3 capture awaits the PixelLab PNG; no fallback screenshots were created.")
		get_tree().quit()
		return
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	if info and info.get_parent():
		info.get_parent().hide()
	var camera := get_node_or_null("ReviewCamera") as Camera3D
	assert(camera != null, "Protagonist context v3 requires Room 1 ReviewCamera.")
	var records: Array[Dictionary] = []
	for view_index in CAPTURE_VIEWS.size():
		_set_view(view_index) # exactly one inherited follow-camera calculation here
		var review_matrix := camera.global_transform
		for mode in [1, 2, 3, 4]:
			_set_mode(mode)
			# Sync copies the already-fixed ReviewCamera for the real viewport and
			# bloom pass; it does not recompute the review camera's follow transform.
			_sync_render_camera()
			_sync_bloom_camera()
			await _frames(12)
			await RenderingServer.frame_post_draw
			var image := get_viewport().get_texture().get_image()
			assert(image.get_width() == 1280 and image.get_height() == 720)
			var filename := "%02d_%s_%s.png" % [view_index + 1, CAPTURE_VIEWS[view_index]["name"], _review_mode_name(mode).replace(" ", "_").replace("#", "").replace("%", "pct")]
			assert(image.save_png(OUT + filename) == OK)
			var actual_camera := render_viewport.get_camera_3d()
			records.append({
				"file": filename,
				"view": CAPTURE_VIEWS[view_index]["name"],
				"review_camera": str(review_matrix),
				"render_camera": str(actual_camera.global_transform) if actual_camera else "",
				"camera_matches_frozen_view": actual_camera.global_transform.is_equal_approx(review_matrix) if actual_camera else false,
				"viewport": [get_viewport().get_texture().get_width(), get_viewport().get_texture().get_height()],
				"internal_viewport": [render_viewport.size.x, render_viewport.size.y],
				"player_position": str(player.global_position),
				"fov": camera.fov if camera else 0.0,
				"appearance": _current_metrics(),
			})
			print("PROTAGONIST_CONTEXT_V3_SHOT ", filename)
	var record_file := FileAccess.open(OUT + "capture_record.json", FileAccess.WRITE)
	record_file.store_string(JSON.stringify({"shots": records, "capture_contract": "Each view sets the inherited player/follow camera once, then captures all four paper modes without recalculating it."}, "\t"))
	record_file.close()
	get_tree().quit()
