extends "res://scripts/dev/cryo_corridor_baked_v2.gd"

const FLOOR_MODEL := preload("res://assets/art/cryo_4f_complete_v3/cryo_4f_complete_v3.glb")
const OTHER_STAIRS := preload("res://assets/art/cryo_4f_complete_v3/other_4f_stairs.glb")
const FLOOR_SHADER := preload("res://scripts/dev/cryo_4f_surface_v3.gdshader")
const FLOOR_GHOST := preload("res://scripts/dev/cryo_4f_ghost_v3.gdshader")
const FLOOR_ROOT := "res://assets/art/cryo_4f_complete_v3/"
var floor_layout: Dictionary = {}
var full_floor_colliders: Array[StaticBody3D] = []
var overview_on := false
var review_zone_index := 0
var portal_transfer_approved := false
var portal_prompt_visible := false
var locked_prompt_visible := false
var nearest_locked_door: Dictionary = {}
var locked_anchor: Node2D
var locked_prompt_owner: Node3D
var portal_barrier: StaticBody3D
var portal_events: Array[Dictionary] = []
var last_locked_interaction: Dictionary = {}
var updating_floor_camera := false
var room_wall_occlusion_enabled := true
var map_labels: Node3D

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():return
	floor_layout=JSON.parse_string(FileAccess.get_file_as_string(FLOOR_ROOT+"layout.json"))
	var old := corridor_sample
	for i in range(occluders.size()-1,-1,-1):
		if old.is_ancestor_of(occluders[i].mesh):occluders.remove_at(i)
	old.visible=false;old.queue_free();baked_materials.clear()
	for mesh in get_node("OutsideRoute").find_children("*","MeshInstance3D",true,false):
		if str(mesh.name).begins_with("R4F_"):mesh.visible=false
	corridor_sample=FLOOR_MODEL.instantiate();corridor_sample.name="Floor4F_ExteriorOnly";add_child(corridor_sample)
	for item in corridor_sample.find_children("*","MeshInstance3D",true,false):
		var mesh := item as MeshInstance3D
		if str(mesh.name)=="Header_D001":mesh.visible=false;continue
		# Long frozen wall boxes cross SW-01: crop their runtime shell portion so
		# the existing Room1 walls/cutaway remain the sole interior representation.
		if str(mesh.name) in ["Shell_W001","Shell_W016","Shell_W017"]:
			var bounds := mesh.get_aabb()
			var lo := bounds.position;var hi := bounds.position+bounds.size
			if str(mesh.name)=="Shell_W016":hi.x=minf(hi.x,0.0)
			else:lo.x=maxf(lo.x,21.0)
			var box := BoxMesh.new();box.size=hi-lo;mesh.mesh=box;mesh.position=(hi+lo)*.5
		var record: Dictionary = floor_layout.receivers.get(str(mesh.name),{})
		if record.is_empty():
			var material := StandardMaterial3D.new()
			material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED
			material.albedo_color=Color(.045,.065,.065)
			mesh.material_override=material
			_register_ghost(mesh,material)
			_attach_solid(mesh)
		else:
			var kind: String = record.kind
			var mat := ShaderMaterial.new();mat.shader=FLOOR_SHADER
			var map_path := "res://assets/art/cryo_corridor_sample_v1/"+("floor.png" if kind=="floor" else "wall.png")
			if kind=="door":map_path="res://assets/art/room1_door_window_r30/door_front.png"
			mat.set_shader_parameter("color_map",load(map_path))
			mat.set_shader_parameter("emission_map",load("res://assets/art/cryo_corridor_sample_v1/wall_emission.png"))
			mat.set_shader_parameter("is_wall",1.0 if kind=="wall" else 0.0)
			mat.set_shader_parameter("lamp_power",1.0)
			mat.set_shader_parameter("baked_energy",1.2)
			mat.set_shader_parameter("irradiance_map",_floor_lightmap())
			mesh.material_override=mat;baked_materials.append(mat)
			if kind!="floor":_register_ghost(mesh,mat)
			else:_attach_solid(mesh)
	var stairs := OTHER_STAIRS.instantiate() as Node3D
	stairs.name="Other4FStairEntrances";add_child(stairs);stairs.position=Vector3(93.2,-11.4,-38.9)
	for mesh in stairs.find_children("*","MeshInstance3D",true,false):
		mesh.material_override=_review_material(Color(.32,.38,.39))
		if "Tread" not in str(mesh.name):_attach_solid(mesh)
	# Black opening is a deliberate interaction boundary, never a walking trigger.
	portal_barrier=StaticBody3D.new();portal_barrier.name="InteractOnlyBlackPortal";portal_barrier.collision_layer=1;portal_barrier.collision_mask=2;add_child(portal_barrier)
	portal_barrier.position=door_closed_position
	var shape := CollisionShape3D.new();var box := BoxShape3D.new();box.size=Vector3(1.4,2.4,.10);shape.shape=box;portal_barrier.add_child(shape)
	locked_anchor=Node2D.new();add_child(locked_anchor)
	locked_prompt_owner=Node3D.new();add_child(locked_prompt_owner)
	map_labels=Node3D.new();map_labels.name="ReviewOnlyRoomEnvelopeLabels";add_child(map_labels);map_labels.visible=false
	for record: Dictionary in floor_layout.rooms:
		var label := Label3D.new();label.text=record.id;label.font_size=48;label.pixel_size=.032
		label.billboard=BaseMaterial3D.BILLBOARD_ENABLED;label.modulate=Color(.72,.86,.86)
		label.position=Vector3((record.x1+record.x2)*.5,3.65,4.2-(record.y1+record.y2)*.5);map_labels.add_child(label)
	set_corridor_lamps(true)
	_update_info()

func _floor_lightmap() -> Texture2D:
	var name := "strip_irradiance.exr" if raw_corridor_light else "strip_irradiance_denoised.exr"
	assert(ResourceLoader.exists(FLOOR_ROOT+name),"Missing matching whole-floor irradiance: "+name)
	return load(FLOOR_ROOT+name)

func _automatic_portal_crossing_enabled() -> bool:
	return false

func _reverse_corridor_controls() -> bool:
	return corridor_view and player and absf(player.position.y)<.3 and _on_floor_walkway(player.position)

func _attach_solid(mesh: MeshInstance3D) -> void:
	var body := StaticBody3D.new();body.name="Solid4F_"+str(mesh.name);body.collision_layer=1;body.collision_mask=2
	mesh.add_child(body);var shape := CollisionShape3D.new();shape.shape=mesh.mesh.create_trimesh_shape();body.add_child(shape);full_floor_colliders.append(body)

func _register_ghost(mesh: MeshInstance3D, original: Material) -> void:
	var ghost: Material=original.duplicate()
	if ghost is ShaderMaterial:
		ghost.shader=FLOOR_GHOST;baked_materials.append(ghost)
	else:
		ghost.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;ghost.albedo_color.a=.12
	occluders.append({"mesh":mesh,"originals":[original],"faded":[ghost],"active":false,"override":original})

func set_corridor_raw(enabled: bool) -> void:
	raw_corridor_light=enabled
	for mat in baked_materials:mat.set_shader_parameter("irradiance_map",_floor_lightmap())
	_update_info()

func update_follow_camera() -> void:
	updating_floor_camera=true
	super.update_follow_camera()
	updating_floor_camera=false
	if not has_node("ReviewCamera"):return
	var camera := $ReviewCamera as Camera3D
	if map_labels:map_labels.visible=overview_on
	if overview_on:
		camera.far=300.0
		camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=208
		camera.keep_aspect=Camera3D.KEEP_WIDTH
		camera.position=Vector3(93.2,155,-38.9);camera.look_at(Vector3(93.2,0,-38.9),Vector3.FORWARD)
	else:
		camera.far=100.0
		camera.projection=Camera3D.PROJECTION_PERSPECTIVE
		if corridor_view and player and absf(player.position.y)<.3 and _on_floor_walkway(player.position):
			camera.position=player.position+Vector3(0,camera_height_m,-camera_distance_m)
			camera.look_at(player.position+Vector3(0,focus_height_m,0),Vector3.UP)
	_update_occlusion()

func _on_floor_walkway(point: Vector3) -> bool:
	for r in floor_layout.get("walk_rects",[]):
		if point.x>=r[0]-.25 and point.x<=r[2]+.25 and 4.2-point.z>=r[1]-.25 and 4.2-point.z<=r[3]+.25:return true
	return false

func _update_occlusion() -> void:
	if updating_floor_camera:return
	if overview_on or not room_wall_occlusion_enabled:
		for entry in occluders:
			if not entry.active:continue
			entry.active=false;entry.alpha=1.0;entry.mesh.material_override=entry.override
			for i in entry.originals.size():entry.mesh.set_surface_override_material(i,entry.originals[i])
		return
	super._update_occlusion()

func _occlusion_probe_offsets() -> Array[Vector3]:
	var points := super._occlusion_probe_offsets()
	for x in [-4.0,-2.0,0.0,2.0,4.0]:points.append(Vector3(x,3.35,0))
	return points

func _process(delta: float) -> void:
	super._process(delta)
	if not locked_anchor or not player:return
	var show := _near_authentication_door() and door_fraction>=.99 and not switching_view
	if show!=portal_prompt_visible:
		portal_prompt_visible=show
		if show:review_ui.show_interaction_name(door_sensor,"E：休眠室へ" if corridor_view else "E：廊下へ",exit_anchor,Vector2(0,-35))
		else:review_ui.hide_interaction_name(door_sensor)
	nearest_locked_door={}
	if corridor_view and not overview_on:
		var distance := 1.5
		for d: Dictionary in floor_layout.get("doors",[]):
			if not d.locked:continue
			var p := Vector3(d.godot[0],0,d.godot[2]);var current := Vector2(player.position.x-p.x,player.position.z-p.z).length()
			if current<distance:distance=current;nearest_locked_door=d
	var locked_show := not nearest_locked_door.is_empty() and not switching_view
	if locked_show:
		var p: Array=nearest_locked_door.godot
		locked_anchor.position=$ReviewCamera.unproject_position(Vector3(p[0],1.2,p[2]))
	if locked_show!=locked_prompt_visible:
		locked_prompt_visible=locked_show
		if locked_show:review_ui.show_interaction_name(locked_prompt_owner,"E：ドア",locked_anchor,Vector2(0,-35))
		else:review_ui.hide_interaction_name(locked_prompt_owner)

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact") and not switching_view and review_ui.can_accept_world_interaction():
		if _near_authentication_door() and door_fraction>=.99:
			portal_transfer_approved=true;_switch_view(not corridor_view);get_viewport().set_input_as_handled();return
		if not nearest_locked_door.is_empty():
			var elevator: bool = nearest_locked_door.kind=="elevator"
			last_locked_interaction={"id":nearest_locked_door.id,"kind":nearest_locked_door.kind,"outcome":"stopped" if elevator else "denied"}
			review_ui.show_text("非常電源モード。人員昇降機は停止している。" if elevator else "この区画へのアクセス権限がない。")
			get_viewport().set_input_as_handled();return
	super._unhandled_input(event)

func _switch_view(outside: bool) -> void:
	if not portal_transfer_approved:return
	portal_transfer_approved=false;switching_view=true
	portal_prompt_visible=false;review_ui.hide_interaction_name(door_sensor)
	portal_events.append({"event":"portal_interact","outside":outside})
	camera_events.append({"event":"fade_out","outside":outside})
	var tween := create_tween();tween.tween_property(fade_rect,"color:a",1.0,.22);await tween.finished
	portal_events.append({"event":"transfer_under_black","alpha":fade_rect.color.a,"outside":outside})
	corridor_view=outside
	teleport_player(Vector3(10.5,.05,-10.7 if outside else -8.2));player.velocity=Vector3.ZERO
	authentication_requested=true;update_follow_camera();_sync_render_camera();_sync_bloom_camera()
	camera_events.append({"event":"rotated_under_black","outside":outside,"alpha":fade_rect.color.a})
	await get_tree().create_timer(.08).timeout
	tween=create_tween();tween.tween_property(fade_rect,"color:a",0.0,.30);await tween.finished
	switching_view=false;input_release_required=true
	camera_events.append({"event":"fade_in_complete","outside":outside})

func review_teleport(point: Vector3) -> void:
	overview_on=false;corridor_view=true;nearest_locked_door={};teleport_player(point);update_follow_camera()

func _update_info() -> void:
	super._update_info()
	if info:info.text="4F整层外壳/走廊 v3 · 其他47间无舱内\nE认证 → 门开后E穿过黑门洞 · F7遮挡透明 · F8门外 · F11整层俯视 · F12审查切区（不授予游戏权限） · F9灯带 · F10 raw/降噪"

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode==KEY_F7:
			room_wall_occlusion_enabled=not room_wall_occlusion_enabled;_update_occlusion();get_viewport().set_input_as_handled();return
		if event.physical_keycode==KEY_F11:
			overview_on=not overview_on;update_follow_camera();get_viewport().set_input_as_handled();return
		if event.physical_keycode==KEY_F8:
			review_teleport(Vector3(10.5,.05,-10.7));get_viewport().set_input_as_handled();return
		if event.physical_keycode==KEY_F12:
			review_zone_index=(review_zone_index+1)%4
			var r: Array=floor_layout.walk_rects[review_zone_index*2]
			var point := Vector3(10.5 if review_zone_index%2==0 else 175.9,.05,4.2-(r[1]+r[3])*.5)
			review_teleport(point);get_viewport().set_input_as_handled();return
	super._unhandled_key_input(event)
