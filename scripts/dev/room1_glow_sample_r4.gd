@tool
extends "res://scripts/dev/room1_glow_sample_r3.gd"

var diffuse_on := true
var bloom_source: SubViewport
var bloom_camera: Camera3D
var bloom_material: ShaderMaterial
var bloom_overlay: TextureRect
var blur_viewports: Array[SubViewport] = []

func _ready() -> void:
	super._ready()
	if not Engine.is_editor_hint():
		_build_bloom()
	apply_sample_state()

func _process(_delta: float) -> void:
	if bloom_camera:
		_sync_bloom_camera()

func _build_bloom() -> void:
	bloom_source = _viewport("ScreenBloomSource")
	bloom_source.own_world_3d = true
	var world := Node3D.new()
	bloom_source.add_child(world)
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color.BLACK
	environment.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world.add_child(environment)
	bloom_camera = Camera3D.new()
	world.add_child(bloom_camera)
	bloom_camera.current = true
	# Black depth occluders prevent hidden screens from glowing through room/pods.
	var black := StandardMaterial3D.new()
	black.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	black.albedo_color = Color.BLACK
	black.cull_mode = BaseMaterial3D.CULL_DISABLED
	var screen := $Pods/P12.find_child("pod_v3_display", true, false) as MeshInstance3D
	for original: MeshInstance3D in find_children("*", "MeshInstance3D", true, false):
		if original.mesh == null or original == screen or original.name == "pod_v3_glass" or original.name == "WindowInteriorGlowCandidate":
			continue
		if not original.is_visible_in_tree() or original.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
			continue
		var occluder := MeshInstance3D.new()
		occluder.mesh = original.mesh
		occluder.material_override = black
		world.add_child(occluder)
		occluder.global_transform = original.global_transform
	var emitter := MeshInstance3D.new()
	emitter.mesh = screen.mesh
	bloom_material = ShaderMaterial.new()
	bloom_material.shader = preload("res://scripts/dev/room1_screen_bloom_source_r4.gdshader")
	bloom_material.set_shader_parameter("screen_pixels", screen_materials["P12"].albedo_texture)
	emitter.material_override = bloom_material
	world.add_child(emitter)
	emitter.global_transform = screen.global_transform
	var near_horizontal := _blur("NearHorizontal", bloom_source.get_texture(), Vector2.RIGHT, 2.0)
	var near_vertical := _blur("NearVertical", near_horizontal.get_texture(), Vector2.DOWN, 2.0)
	var far_horizontal := _blur("FarHorizontal", bloom_source.get_texture(), Vector2.RIGHT, 7.0)
	var far_vertical := _blur("FarVertical", far_horizontal.get_texture(), Vector2.DOWN, 7.0)
	var layer := CanvasLayer.new()
	layer.layer = 5
	add_child(layer)
	bloom_overlay = TextureRect.new()
	bloom_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bloom_overlay.texture = bloom_source.get_texture()
	bloom_overlay.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	var composite := ShaderMaterial.new()
	composite.shader = preload("res://scripts/dev/room1_bloom_composite_r4.gdshader")
	composite.set_shader_parameter("near_halo", near_vertical.get_texture())
	composite.set_shader_parameter("far_halo", far_vertical.get_texture())
	bloom_overlay.material = composite
	layer.add_child(bloom_overlay)
	_sync_bloom_camera()

func _viewport(label: String) -> SubViewport:
	var viewport := SubViewport.new()
	viewport.name = label
	viewport.size = Vector2i(320, 180)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.gui_disable_input = true
	add_child(viewport)
	blur_viewports.append(viewport)
	return viewport

func _blur(label: String, source: Texture2D, axis: Vector2, sigma: float) -> SubViewport:
	var viewport := _viewport(label)
	viewport.disable_3d = true
	var rect := TextureRect.new()
	rect.texture = source
	rect.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var material := ShaderMaterial.new()
	material.shader = preload("res://scripts/dev/room1_gaussian_blur_r4.gdshader")
	material.set_shader_parameter("direction", axis)
	material.set_shader_parameter("sigma", sigma)
	rect.material = material
	viewport.add_child(rect)
	return viewport

func _sync_bloom_camera() -> void:
	var camera := $ReviewCamera as Camera3D
	bloom_camera.global_transform = camera.global_transform
	bloom_camera.projection = camera.projection
	bloom_camera.keep_aspect = camera.keep_aspect
	bloom_camera.fov = camera.fov
	bloom_camera.size = camera.size
	bloom_camera.near = camera.near
	bloom_camera.far = camera.far
	var full_size := Vector2i(get_viewport().get_visible_rect().size)
	var quarter_size := Vector2i(maxi(full_size.x / 4, 1), maxi(full_size.y / 4, 1))
	for viewport in blur_viewports:
		viewport.size = quarter_size
	bloom_overlay.size = Vector2(full_size)

func apply_sample_state() -> void:
	super.apply_sample_state()
	if soft_screen and diffuse_on:
		soft_screen.shader = preload("res://scripts/dev/room1_screen_diffuse_core_r4.gdshader")
	# Use the custom diffusion alone in the new candidate; the native kernel
	# was filling the panel into a bright rectangle. F restores the r3 treatment.
	$WorldEnvironment.environment.glow_enabled = halo_on and not diffuse_on
	if bloom_overlay:
		bloom_overlay.visible = diffuse_on and halo_on and screens_on
		bloom_material.set_shader_parameter("powered", 1.0 if screens_on else 0.0)
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	super._unhandled_key_input(event)
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_F:
		diffuse_on = not diffuse_on
		apply_sample_state()

func _update_info() -> void:
	if info:
		info.text = "荧光小样 r4 / 清楚文字＋向外扩散 · 待审\n1屏幕 2舱窗 3整舱 4室内\nF新旧对照 %s · N光晕 %s · P附近投光 · B屏幕 · H说明\n玻璃沿用r2；像素接缝后续处理。本地小样。" % [diffuse_on, halo_on]
