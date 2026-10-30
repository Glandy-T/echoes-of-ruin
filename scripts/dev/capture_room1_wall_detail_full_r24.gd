extends Node

const OUT := "res://docs/art/experiments/room1_wall_detail_full_r24/evidence/"
var room:Node3D
var camera:Camera3D
var hero:Node3D
var records:Array[Dictionary]=[]
var follow_fov:=0.0
var screen_overlays_frozen:=false
var occluders_hidden:=false

func _ready() -> void:call_deferred("capture")
func look(position:Vector3,target:Vector3,fov:float) -> void:
	camera.global_position=position;camera.look_at(target,Vector3.UP);camera.fov=fov
func shot(name:String) -> void:
	room._sync_render_camera();room._sync_bloom_camera();room._sync_standard_visuals()
	room._sync_complete_room_pose();room._sync_complete_screen_sources();room._sync_door_glow()
	for _i in 12:await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image:=get_viewport().get_texture().get_image()
	assert(image.save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","mode":room.r24_mode,"p12_pose":hero.get_state_name(),"camera":str(camera.global_transform),"fov":camera.fov,"resolution":[image.get_width(),image.get_height()],"screen_overlays_frozen":screen_overlays_frozen,"occluders_hidden":occluders_hidden})
	print("R24_SHOT ",name)

func freeze_screen_overlays() -> void:
	for pod:Node3D in room.room_pods.values():
		var viewport:SubViewport=pod.get("_screen_viewport")
		if viewport:viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
	screen_overlays_frozen=true
func set_base_color(enabled:float) -> void:
	for material:ShaderMaterial in room.complete_shell_materials:material.set_shader_parameter("base_color_preview",enabled)
func follow_view(point:Vector3) -> void:
	room.teleport_player(point);camera.fov=follow_fov
	await get_tree().process_frame

func with_front_wall_visible(prefix:String) -> void:
	var front:MeshInstance3D=room.get_node("Shell").find_child("Wall_front",true,false)
	var old_visible:=front.visible;var old_shadow:=front.cast_shadow
	front.visible=true;front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	# Both front corners plus the wide technical view prove the normally-cut wall
	# and its lamp slot are actually rendered rather than merely existing outside frame.
	for view:Array in [["corner_front_left",Vector3(2.5,1.9,-3.2),Vector3(.2,1.45,-.25),70.0],["corner_front_right",Vector3(18.5,1.9,-3.2),Vector3(20.8,1.45,-.25),70.0],["front_wall_full",Vector3(10.5,2.2,-5.7),Vector3(10.5,1.55,-.2),70.0]]:
		look(view[1],view[2],view[3]);await shot(prefix+view[0])
	front.visible=old_visible;front.cast_shadow=old_shadow

func full_wall_views(prefix:String) -> void:
	# Each frame includes lamp/upper finish through lower protection band for its
	# assigned wall, using rendered visibility rather than off-camera coverage.
	look(Vector3(1.7,1.72,-5.25),Vector3(.2,1.30,-6.9),57.0);await shot(prefix+"left_wall_full")
	look(Vector3(19.3,1.72,-5.25),Vector3(20.8,1.30,-6.9),57.0);await shot(prefix+"right_wall_full")
	look(Vector3(10.5,2.2,-4.65),Vector3(10.5,1.55,-9.28),68.0);await shot(prefix+"rear_wall_full")
	look(Vector3(10.5,2.55,-4.3),Vector3(10.5,2.1,-9.25),60.0);await shot(prefix+"door_header_and_sides")

func normal_and_corner_views(prefix:String) -> void:
	for row:Array in [["front",-4.75],["back",-8.0]]:
		for column:Array in [["left",3.525],["middle",10.5],["right",17.475]]:
			await follow_view(Vector3(column[1],.05,row[1]));await shot(prefix+"game_"+str(row[0])+"_"+str(column[0])+"_closed")
	for view:Array in [["corner_rear_left",Vector3(2.5,1.9,-6.2),Vector3(.2,1.45,-9.25),60.0],["corner_rear_right",Vector3(18.5,1.9,-6.2),Vector3(20.8,1.45,-9.25),60.0]]:
		look(view[1],view[2],view[3]);await shot(prefix+view[0])

func snapshot_visibility(node:Node, snapshots:Array[Dictionary]) -> void:
	if node is Node3D:
		snapshots.append({"node":node,"visible":(node as Node3D).visible})
func hide_scan_occluders() -> Array[Dictionary]:
	# These are capture-only visibility overrides.  The pod parent removes every
	# physical pod; independent bloom/display copies must be hidden too, otherwise
	# an apparent black silhouette would invalidate the wall scan.
	var snapshots:Array[Dictionary]=[]
	var pods:Node3D=room.get_node("Pods") as Node3D
	snapshot_visibility(pods,snapshots);pods.visible=false
	snapshot_visibility(room.standard,snapshots);room.standard.visible=false
	for item:Dictionary in room.standard_bloom_meshes:
		if is_instance_valid(item.clone):
			snapshot_visibility(item.clone,snapshots);(item.clone as Node3D).visible=false
	for proxy in room.screen_proxies.values():
		if is_instance_valid(proxy):
			snapshot_visibility(proxy,snapshots);(proxy as Node3D).visible=false
	occluders_hidden=true
	return snapshots
func restore_scan_occluders(snapshots:Array[Dictionary]) -> void:
	for item:Dictionary in snapshots:
		if is_instance_valid(item.node):(item.node as Node3D).visible=bool(item.visible)
	occluders_hidden=false

func wall_scan_views(prefix:String) -> void:
	# Full-height, overlapping technical scan.  These are intentionally separate
	# from gameplay views: no wall panel may claim coverage while blocked or out of frame.
	var snapshots:=hide_scan_occluders()
	var front:MeshInstance3D=room.get_node("Shell").find_child("Wall_front",true,false)
	var front_visible:=front.visible;var front_shadow:=front.cast_shadow
	front.visible=true;front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for i in range(4):
		var x:=2.4+5.4*i
		look(Vector3(x,1.8,-5.8),Vector3(x,1.7,-.2),68.0);await shot(prefix+"scan_front_%02d"%(i+1))
	front.visible=front_visible;front.cast_shadow=front_shadow
	for i in range(4):
		var x:=2.4+5.4*i
		look(Vector3(x,1.8,-3.68),Vector3(x,1.7,-9.28),68.0);await shot(prefix+"scan_rear_%02d"%(i+1))
	for i in range(2):
		var z:=-2.6-4.4*i
		look(Vector3(6.5,1.8,z),Vector3(.2,1.7,z),68.0);await shot(prefix+"scan_left_%02d"%(i+1))
		look(Vector3(14.5,1.8,z),Vector3(20.8,1.7,z),68.0);await shot(prefix+"scan_right_%02d"%(i+1))
	restore_scan_occluders(snapshots)

func base_color_diagnostics() -> void:
	set_base_color(1.0);hero.set_open_immediate(false)
	look(Vector3(1.7,1.72,-5.25),Vector3(.2,1.30,-6.9),57.0);await shot("2_base_color_left_wall")
	look(Vector3(19.3,1.72,-5.25),Vector3(20.8,1.30,-6.9),57.0);await shot("2_base_color_right_wall")
	look(Vector3(10.5,2.2,-4.65),Vector3(10.5,1.55,-9.28),68.0);await shot("2_base_color_rear_wall")
	await with_front_wall_visible("2_base_color_")
	set_base_color(0.0)

func raw_denoised_material_diagnostics() -> void:
	# Existing r19 EXRs are not rebaked.  This verifies the new wall maps under
	# both existing endpoints and restores denoised afterward.
	for raw:bool in [true,false]:
		room.set_complete_lightmaps(raw)
		var label:="raw" if raw else "denoised"
		look(Vector3(10.5,2.55,-4.3),Vector3(10.5,2.1,-9.25),60.0);await shot("2_"+label+"_door_header")
		look(Vector3(2.5,1.9,-6.2),Vector3(.2,1.45,-9.25),60.0);await shot("2_"+label+"_rear_corner")
	room.set_complete_lightmaps(false)

func capture() -> void:
	room=get_parent() as Node3D
	assert(room._r24_assets_available(),"r24 capture requires final all-wall PixelLab assets")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for _i in 120:await get_tree().process_frame
	room.finish_exit();room.review_ui.close_dialogue();room.actor_shadow_on=false;room._sync_actor_shadow()
	for _i in 60:await get_tree().process_frame
	for key:String in ["paper_hero","bloom_paper_hero"]:
		var actor:Sprite3D=room.get(key)
		if actor:actor.visible=false
	room.info.get_parent().hide()
	if room.review_ui.get("pause_button"):(room.review_ui.get("pause_button") as Control).hide()
	camera=room.get_node("ReviewCamera") as Camera3D;hero=room.room_pods["P12"];follow_fov=camera.fov
	freeze_screen_overlays()
	# Never let the inherited controller overwrite technical camera transforms.
	room.set_process(false);room.set_physics_process(false)
	for mode:int in [1,2]:
		room.set_r24_mode(mode);hero.set_open_immediate(false)
		await normal_and_corner_views("%d_"%mode)
		await with_front_wall_visible("%d_"%mode)
		await full_wall_views("%d_"%mode)
		await wall_scan_views("%d_"%mode)
		hero.set_open_immediate(true)
		await follow_view(Vector3(3.525,.05,-4.75));await shot("%d_game_front_left_open"%mode)
		look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44.0);await shot("%d_p12_oblique_open"%mode)
	room.set_r24_mode(1);hero.set_open_immediate(false)
	look(Vector3(10.5,2.2,-4.65),Vector3(10.5,1.55,-9.28),68.0);await shot("1_restore_rear_wall_closed")
	room.set_r24_mode(2);await base_color_diagnostics();await raw_denoised_material_diagnostics()
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
