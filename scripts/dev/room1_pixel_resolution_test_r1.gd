@tool
extends "res://scripts/dev/room1_player_physics_test_r1.gd"

const PIXEL_SIZES := [Vector2i(1280, 720), Vector2i(640, 360), Vector2i(426, 240)]
var pixel_mode := 1
var render_viewport: SubViewport
var render_camera: Camera3D
var presentation: TextureRect
var presentation_back: ColorRect

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	render_viewport = SubViewport.new()
	render_viewport.name = "PixelSceneViewport"
	render_viewport.world_3d = get_world_3d()
	render_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	render_viewport.gui_disable_input = true
	add_child(render_viewport)
	render_camera = Camera3D.new()
	render_viewport.add_child(render_camera)
	render_camera.current = true
	# Composite the existing soft screen glow before nearest-neighbor enlargement.
	if bloom_overlay:
		bloom_overlay.get_parent().reparent(render_viewport)
	var layer := CanvasLayer.new()
	layer.layer = -5
	add_child(layer)
	presentation_back = ColorRect.new()
	presentation_back.color = Color.BLACK
	presentation_back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(presentation_back)
	presentation = TextureRect.new()
	presentation.texture = render_viewport.get_texture()
	presentation.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	presentation.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	presentation.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(presentation)
	get_viewport().disable_3d = true
	set_pixel_mode(pixel_mode)

func set_pixel_mode(index: int) -> void:
	pixel_mode = clampi(index, 0, 2)
	if render_viewport:
		render_viewport.size = PIXEL_SIZES[pixel_mode]
		_layout_presentation()
		_sync_render_camera()
		_sync_bloom_camera()
	_update_info()

func _layout_presentation() -> void:
	var output_size := get_viewport().get_visible_rect().size
	var internal := Vector2(PIXEL_SIZES[pixel_mode])
	var fit := minf(output_size.x / internal.x, output_size.y / internal.y)
	var factor := fit
	presentation.size = internal * factor
	presentation.position = ((output_size - presentation.size) * 0.5).floor()
	presentation_back.size = output_size

func _sync_render_camera() -> void:
	var source := $ReviewCamera as Camera3D
	render_camera.global_transform = source.global_transform
	render_camera.projection = source.projection
	render_camera.keep_aspect = source.keep_aspect
	render_camera.fov = source.fov
	render_camera.size = source.size
	render_camera.near = source.near
	render_camera.far = source.far

func _sync_bloom_camera() -> void:
	super._sync_bloom_camera()
	if render_viewport and bloom_overlay:
		# Keep blur input resolution/radius identical, then downsample the result
		# into the scene viewport. Only the presentation pixel grid changes.
		bloom_overlay.size = Vector2(render_viewport.size)

func _process(delta: float) -> void:
	super._process(delta)
	if render_camera:
		_sync_render_camera()
		_layout_presentation()

func _unhandled_key_input(event: InputEvent) -> void:
	super._unhandled_key_input(event)
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_F1: set_pixel_mode(0)
		KEY_F2: set_pixel_mode(1)
		KEY_F3: set_pixel_mode(2)

func _update_info() -> void:
	if info:
		var size: Vector2i = PIXEL_SIZES[pixel_mode]
		info.text = "Room 1 / 渲染像素密度对照 · 待审\nF1原画1280×720 · F2中640×360 · F3粗426×240\n当前 %d×%d，最近邻放大；说明文字保持清晰\nWASD移动 · R复位 · K阴影 · C碰撞 · L灯带 · H说明" % [size.x, size.y]

