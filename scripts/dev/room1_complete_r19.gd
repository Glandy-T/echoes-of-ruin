extends "res://scripts/dev/room1_door_soft_glow_r18.gd"

const COMPLETE_LAYOUT:="res://assets/art/room1_complete_r19/layout.json"
const COMPLETE_LIGHTS:="res://assets/art/room1_complete_r19/lighting/"
const COMPLETE_SURFACE:=preload("res://scripts/dev/room1_complete_surface_r19.gdshader")
const COMPLETE_SCREEN:=preload("res://scripts/props/cryopod_complete_screen_r19.gdshader")
var room_pods:Dictionary={}
var room_pod_finishes:Dictionary={}
var room_pod_records:Array=[]
var room_screen_sources:Dictionary={}
var complete_ready:=false
var complete_raw_lightmaps:=false
var complete_shell_materials:Array[ShaderMaterial]=[]
var complete_room_closed:Texture2D
var complete_room_open:Texture2D
var complete_binding_report:Dictionary={}

func _build_door_glow() -> void:
	# r18 calls this only after r16 has finished constructing P12. Replace the
	# other pods before the door halo takes its depth-occluder snapshot.
	_install_complete_room()
	super._build_door_glow()

func _install_complete_room() -> void:
	assert(FileAccess.file_exists(COMPLETE_LAYOUT),"Missing r19 layout contract.")
	var layout:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(COMPLETE_LAYOUT))
	room_pod_records=layout.pods
	assert(room_pod_records.size()==20)
	for record:Dictionary in room_pod_records:
		var id:String=record.id
		var old:Node3D=$Pods.get_node(id)
		var origin:=Vector3(record.origin[0],record.origin[1],record.origin[2])
		assert(old.global_position.distance_to(origin)<0.001,"Bake/layout mismatch: "+id)
		old.visible=false
		for solid:CollisionObject3D in old.find_children("*","CollisionObject3D",true,false):
			solid.collision_layer=0;solid.collision_mask=0
			for shape:CollisionShape3D in solid.find_children("*","CollisionShape3D",true,false):shape.disabled=true
		var pod:Node3D=standard if record.number==12 else STANDARD.instantiate()
		if record.number!=12:
			# No placement ever briefly adopts P12's private lightmaps.
			pod.closed_irradiance=null;pod.open_irradiance=null
			pod.name=id+"_StandardV8"
			pod.transform=$Pods.global_transform.affine_inverse()*old.global_transform
			$Pods.add_child(pod)
			pod.set_open_immediate(false)
		var finish:RefCounted=pod_finish if record.number==12 else POD_FINISH.new(pod,int(record.number))
		finish.apply(int(record.variant_index),true)
		# Use the exact exported numbered images which also feed the bake.
		for entry:Dictionary in finish.entries:
			entry.material.set_shader_parameter("color_map",load("res://"+str(record.bake_color_maps[entry.role])))
		room_pods[id]=pod;room_pod_finishes[id]=finish
		if id in ["P02","P17"]:_apply_warning_screen(pod)
		pod.set_tube_powered(id in ["P02","P12","P17"])
		pod.set_screen_powered(id in ["P02","P12","P17"])
		# Preserve unknown names/metrics; do not invent occupants or new story.
		if record.number!=12:pod.set_screen_state("----","----",0.0,0.0,0.0)
	for name in full_materials:
		if name not in ["Floor_continuous_no_tile_seams","Wall_left","Wall_right","Wall_front","Wall_rear_left","Wall_rear_right","Wall_rear_door_header"]:continue
		for material:ShaderMaterial in full_materials[name]:
			var params:=_copy_parameters(material)
			material.shader=COMPLETE_SURFACE
			for key in params:material.set_shader_parameter(key,params[key])
			complete_shell_materials.append(material)
	complete_ready=true
	set_complete_lightmaps(false)
	_rebuild_complete_screen_bloom()
	apply_sample_state()
	_update_info()

func _apply_warning_screen(pod:Node3D) -> void:
	var display:MeshInstance3D=pod.get_display_mesh()
	for surface in display.mesh.get_surface_count():
		var material:=display.get_active_material(surface) as ShaderMaterial
		var params:Dictionary={}
		for entry:Dictionary in material.shader.get_shader_uniform_list():params[entry.name]=material.get_shader_parameter(entry.name)
		material.shader=COMPLETE_SCREEN
		for key in params:material.set_shader_parameter(key,params[key])
		material.set_shader_parameter("warning_red",1.0)

func _lightmap(name:String) -> Texture2D:
	var path:=COMPLETE_LIGHTS+name+("_raw" if complete_raw_lightmaps else "")+".exr"
	assert(ResourceLoader.exists(path),"Missing matching r19 bake: "+path)
	return load(path) as Texture2D

func set_complete_lightmaps(raw:bool) -> void:
	complete_raw_lightmaps=raw
	if not complete_ready:return
	complete_room_closed=_lightmap("room_closed");complete_room_open=_lightmap("room_open")
	for id:String in room_pods:
		var closed:=_lightmap(id+"_closed")
		var opened:Texture2D=_lightmap("P12_open") if id=="P12" else closed
		room_pods[id].set_pose_lightmaps(closed,opened,continuous_baked_energy if strip_on else 0.0)
	for material in complete_shell_materials:
		material.set_shader_parameter("strip_irradiance",complete_room_closed)
		material.set_shader_parameter("strip_irradiance_open",complete_room_open)
	_sync_complete_room_pose()

func _rebuild_complete_screen_bloom() -> void:
	var world:Node3D=bloom_camera.get_parent()
	for old in world.get_children():
		if old is MeshInstance3D and old!=bloom_actor:
			old.visible=false;old.queue_free()
	standard_bloom_meshes.clear();room_screen_sources.clear()
	var black:=StandardMaterial3D.new()
	black.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
	black.albedo_color=Color.BLACK;black.cull_mode=BaseMaterial3D.CULL_DISABLED
	var displays:Dictionary={}
	for id:String in room_pods:displays[room_pods[id].get_display_mesh()]=id
	for source:MeshInstance3D in find_children("*","MeshInstance3D",true,false):
		if source.is_queued_for_deletion() or source.get_world_3d()!=get_world_3d() or not source.mesh:continue
		if not source.is_visible_in_tree() or source.cast_shadow==GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:continue
		if (source.layers & render_camera.cull_mask)==0 or "Glass" in str(source.name):continue
		var proxy:=MeshInstance3D.new();proxy.mesh=source.mesh
		proxy.material_override=black
		if displays.has(source):
			var id:String=displays[source]
			var material:ShaderMaterial=(source.get_active_material(0) as ShaderMaterial).duplicate()
			material.set_shader_parameter("panel_backlight",0.0)
			material.set_shader_parameter("core_energy",1.0)
			proxy.material_override=material
			room_screen_sources[id]=material
			room_bloom_materials[id]=material
			if id=="P12":standard_bloom_screen=proxy
		world.add_child(proxy)
		proxy.global_transform=source.global_transform
		standard_bloom_meshes.append({"source":source,"clone":proxy})
	_sync_complete_screen_sources()

func _sync_complete_screen_sources() -> void:
	for id:String in room_screen_sources:
		var pod:Node3D=room_pods[id]
		var material:ShaderMaterial=room_screen_sources[id]
		material.set_shader_parameter("screen_pixels",pod.get_screen_texture())
		material.set_shader_parameter("screen_overlay",pod.get_screen_overlay_texture())
		material.set_shader_parameter("powered",1.0 if pod.screen_powered else 0.0)
		material.set_shader_parameter("progress",pod.screen_progress)
		material.set_shader_parameter("secondary_progress",pod.screen_secondary_progress)
		material.set_shader_parameter("tertiary_progress",pod.screen_tertiary_progress)

func _sync_standard_visuals() -> void:
	# Some inherited chunk/preview parents are freed at the end of _ready.
	# Their children were visible during the snapshot but must never remain
	# as dangling sources in the rebuilt whole-room bloom depth set.
	if complete_ready:
		for i in range(standard_bloom_meshes.size()-1,-1,-1):
			var item:Dictionary=standard_bloom_meshes[i]
			if not is_instance_valid(item.source) or not is_instance_valid(item.clone):
				if is_instance_valid(item.clone):item.clone.queue_free()
				standard_bloom_meshes.remove_at(i)
	super._sync_standard_visuals()

func _sync_complete_room_pose() -> void:
	if not complete_ready:return
	var surfaces:Array=standard.get("_surface_materials")
	var blend:float=surfaces[0].get_shader_parameter("pose_blend")
	for material in complete_shell_materials:material.set_shader_parameter("room_pose_blend",blend)

func apply_sample_state() -> void:
	super.apply_sample_state()
	if not complete_ready:return
	for id:String in room_pods:
		var lit:bool=id in ["P02","P12","P17"]
		room_pods[id].set_tube_powered(lit and local_light_on and windows_on)
		room_pods[id].set_screen_powered(lit and screens_on)
		room_pods[id].set_baked_energy(continuous_baked_energy if strip_on else 0.0)
		window_proxies[id].visible=false;window_proxies[id].light_energy=0.0
		var display:MeshInstance3D=room_pods[id].get_display_mesh()
		screen_proxies[id].global_position=display.to_global(display.get_aabb().get_center())
		screen_proxies[id].visible=lit and local_light_on and screens_on
	_sync_complete_screen_sources();_sync_complete_room_pose()

func _sync_actor_shadow() -> void:
	super._sync_actor_shadow()
	if not complete_ready or not actor_mesh:return
	for id:String in room_pods:
		if id=="P12":continue
		room_pods[id].set_actor_shadow_parameters(player.global_position,actor_mesh.global_transform*Vector3(0,-.605,0),actor_mesh.global_transform*Vector3(0,.605,0),actor_shadow_on)

func _process(delta:float) -> void:
	super._process(delta)
	if complete_ready:_sync_complete_screen_sources();_sync_complete_room_pose()

func _unhandled_key_input(event:InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():return
	if not event is InputEventKey or not event.pressed or event.echo:return
	match event.physical_keycode:
		KEY_F4:set_door_glow(not door_glow_on)
		KEY_O:standard.toggle()
		KEY_I:set_complete_lightmaps(not complete_raw_lightmaps)
		KEY_L:strip_on=not strip_on;apply_sample_state()
		KEY_G:local_light_on=not local_light_on;apply_sample_state()
		KEY_B:screens_on=not screens_on;apply_sample_state()
		KEY_V:standard.set_glass_visible(not standard.glass_visible)
		KEY_H:info.get_parent().visible=not info.get_parent().visible
		KEY_0:teleport_player(Vector3(10.5,0.05,-7.7))
		KEY_J:finish_exit();position_structure_review()
		_:return
	get_viewport().set_input_as_handled();_update_info()

func _update_info() -> void:
	if info:info.text="Room 1 / 整室整合 r19\n20舱、独立编号、按位置受光；仅P12可用\nO主角舱盖 · V玻璃 · I原始/降噪光图 · F4门灯柔光 · 0门前 · J舱前\nWASD移动 · E调查 · Enter对白 · Esc暂停"
