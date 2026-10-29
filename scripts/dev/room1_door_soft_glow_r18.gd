extends "res://scripts/dev/room1_door_inner_light_r17.gd"

const HALO_SOURCE:=preload("res://scripts/dev/door_halo_source_r18.gdshader")
const HALO_COMPOSITE:=preload("res://scripts/dev/door_halo_composite_r18.gdshader")
const GAUSSIAN:=preload("res://scripts/dev/room1_gaussian_blur_r4.gdshader")
var door_glow_on:=true
var door_glow_source:SubViewport
var door_glow_camera:Camera3D
var door_glow_material:ShaderMaterial
var door_glow_overlay:TextureRect
var door_glow_views:Array[SubViewport]=[]
var door_glow_proxies:Array[Dictionary]=[]
var door_glow_actor:Sprite3D

func _ready() -> void:
	super._ready()
	_build_door_glow()
	_sync_door_glow()
	_update_info()

func _glow_view(label:String) -> SubViewport:
	var view:=SubViewport.new()
	view.name=label;view.size=render_viewport.size
	view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	view.gui_disable_input=true
	add_child(view);door_glow_views.append(view)
	return view

func _glow_blur(label:String,source:Texture2D,axis:Vector2,sigma:float) -> SubViewport:
	var view:=_glow_view(label);view.disable_3d=true
	var rect:=TextureRect.new();rect.texture=source
	var mat:=ShaderMaterial.new();mat.shader=GAUSSIAN
	mat.set_shader_parameter("direction",axis);mat.set_shader_parameter("sigma",sigma)
	view.add_child(rect);rect.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	rect.material=mat
	return view

func _build_door_glow() -> void:
	door_glow_source=_glow_view("DoorLensVisibleMaskR18")
	door_glow_source.own_world_3d=true
	door_glow_source.msaa_3d=Viewport.MSAA_4X
	var world:=Node3D.new();door_glow_source.add_child(world)
	var environment:=WorldEnvironment.new();environment.environment=Environment.new()
	environment.environment.background_mode=Environment.BG_COLOR
	environment.environment.background_color=Color.BLACK
	environment.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	world.add_child(environment)
	door_glow_camera=Camera3D.new();world.add_child(door_glow_camera)
	door_glow_camera.current=true
	var black:=StandardMaterial3D.new()
	black.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	black.albedo_color=Color.BLACK;black.cull_mode=BaseMaterial3D.CULL_DISABLED
	door_glow_material=ShaderMaterial.new();door_glow_material.shader=HALO_SOURCE
	# Independent depth mask: include actual moving leaf and current room/pods.
	# Never borrow an old placeholder door or add emitters to the screen bloom.
	for original:MeshInstance3D in find_children("*","MeshInstance3D",true,false):
		if original.is_queued_for_deletion():continue
		if original.get_world_3d()!=get_world_3d() or not original.mesh:continue
		if not original.is_visible_in_tree():continue
		if original.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:continue
		if (original.layers & render_camera.cull_mask)==0:continue
		var proxy:=MeshInstance3D.new();proxy.mesh=original.mesh
		proxy.material_override=door_glow_material if original in inner_lights else black
		world.add_child(proxy)
		door_glow_proxies.append({"source":original,"proxy":proxy})
	if paper_hero:
		door_glow_actor=Sprite3D.new();door_glow_actor.modulate=Color(0,0,0,1)
		door_glow_actor.texture=paper_hero.texture
		door_glow_actor.hframes=paper_hero.hframes;door_glow_actor.vframes=paper_hero.vframes
		door_glow_actor.pixel_size=paper_hero.pixel_size
		door_glow_actor.centered=paper_hero.centered;door_glow_actor.offset=paper_hero.offset
		door_glow_actor.billboard=paper_hero.billboard
		world.add_child(door_glow_actor)
	var near_h:=_glow_blur("DoorGlowNearH",door_glow_source.get_texture(),Vector2.RIGHT,1.7)
	var near_v:=_glow_blur("DoorGlowNearV",near_h.get_texture(),Vector2.DOWN,1.7)
	var far_h:=_glow_blur("DoorGlowFarH",door_glow_source.get_texture(),Vector2.RIGHT,3.5)
	var far_v:=_glow_blur("DoorGlowFarV",far_h.get_texture(),Vector2.DOWN,3.5)
	var layer:=CanvasLayer.new();layer.name="DoorSoftGlowR18";layer.layer=6
	render_viewport.add_child(layer)
	door_glow_overlay=TextureRect.new();layer.add_child(door_glow_overlay)
	door_glow_overlay.mouse_filter=Control.MOUSE_FILTER_IGNORE
	door_glow_overlay.texture=door_glow_source.get_texture()
	var composite:=ShaderMaterial.new();composite.shader=HALO_COMPOSITE
	composite.set_shader_parameter("near_halo",near_v.get_texture())
	composite.set_shader_parameter("far_halo",far_v.get_texture())
	composite.set_shader_parameter("visible_core",door_glow_source.get_texture())
	door_glow_overlay.material=composite

func set_door_glow(enabled:bool) -> void:
	door_glow_on=enabled
	_sync_door_glow();_update_info()

func _sync_door_glow() -> void:
	if not is_instance_valid(door_glow_overlay):return
	door_glow_overlay.visible=door_glow_on and inner_light_fixed
	door_glow_overlay.size=Vector2(render_viewport.size)
	for view in door_glow_views:
		if view.size!=render_viewport.size:view.size=render_viewport.size
	door_glow_camera.global_transform=render_camera.global_transform
	door_glow_camera.projection=render_camera.projection
	door_glow_camera.keep_aspect=render_camera.keep_aspect
	door_glow_camera.fov=render_camera.fov;door_glow_camera.size=render_camera.size
	door_glow_camera.near=render_camera.near;door_glow_camera.far=render_camera.far
	for key in ["passage_power","leaf_min_x","leaf_max_x","phosphor_color","phosphor_energy"]:
		door_glow_material.set_shader_parameter(key,inner_light_material.get_shader_parameter(key))
	for i in range(door_glow_proxies.size()-1,-1,-1):
		var item:Dictionary=door_glow_proxies[i]
		if not is_instance_valid(item.source):
			item.proxy.queue_free();door_glow_proxies.remove_at(i);continue
		item.proxy.global_transform=item.source.global_transform
		item.proxy.visible=item.source.is_visible_in_tree()
	if door_glow_actor:
		door_glow_actor.global_transform=paper_hero.global_transform
		if door_glow_actor.texture!=paper_hero.texture or door_glow_actor.hframes!=paper_hero.hframes or door_glow_actor.vframes!=paper_hero.vframes:
			# Idle has 4 frames, walk has 6; switch the sheet before its frame.
			door_glow_actor.frame=0
			door_glow_actor.texture=paper_hero.texture
			door_glow_actor.hframes=paper_hero.hframes;door_glow_actor.vframes=paper_hero.vframes
		door_glow_actor.frame=paper_hero.frame;door_glow_actor.flip_h=paper_hero.flip_h
		door_glow_actor.visible=paper_hero.is_visible_in_tree()

func _process(delta:float) -> void:
	super._process(delta)
	_sync_door_glow()

func _unhandled_key_input(event:InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode==KEY_F4:
		set_door_glow(not door_glow_on);get_viewport().set_input_as_handled();return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:info.text="Room 1 / 门灯柔光 r18\nF4："+("窄灯芯＋薄柔光" if door_glow_on else "r17仅窄灯芯")+"\n颜色、灯槽和通行遮挡保持；只扩散可见灯芯。"
