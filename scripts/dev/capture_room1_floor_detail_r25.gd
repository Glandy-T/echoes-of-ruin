extends Node

const OUT := "res://docs/art/experiments/room1_floor_detail_r25/evidence/"
var room:Node3D
var camera:Camera3D
var hero:Node3D
var records:Array[Dictionary]=[]
var follow_fov:=0.0
var overlays_frozen:=false
var pods_hidden:=false

func _ready() -> void:call_deferred("capture")
func look(position:Vector3,target:Vector3,fov:float) -> void:
	camera.global_position=position;camera.look_at(target,Vector3.UP);camera.fov=fov
func shot(name:String,diagnostic:bool=false) -> void:
	room._sync_render_camera();room._sync_bloom_camera();room._sync_standard_visuals()
	room._sync_complete_room_pose();room._sync_complete_screen_sources();room._sync_door_glow()
	for _i in 12:await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image:=get_viewport().get_texture().get_image()
	assert(image.save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","mode":room.r25_mode,"p12_pose":hero.get_state_name(),"camera":str(camera.global_transform),"fov":camera.fov,"resolution":[image.get_width(),image.get_height()],"overlays_frozen":overlays_frozen,"pods_hidden":pods_hidden,"diagnostic":diagnostic})
	print("R25_SHOT ",name)
func freeze_overlays() -> void:
	for pod:Node3D in room.room_pods.values():
		var viewport:SubViewport=pod.get("_screen_viewport")
		if viewport:viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
	overlays_frozen=true
func set_base_color(enabled:float) -> void:
	for material:ShaderMaterial in room.complete_shell_materials:material.set_shader_parameter("base_color_preview",enabled)
func follow_view(point:Vector3) -> void:
	room.teleport_player(point);camera.fov=follow_fov
	await get_tree().process_frame
func floor_patch_views(prefix:String) -> void:
	# P12/P13 border, their contact area, leak-side residue and a small central
	# aisle all fit the fixed r25 patch. Normal views intentionally retain pods.
	await follow_view(Vector3(4.2,.05,-5.35));await shot(prefix+"game_floor_patch_closed")
	look(Vector3(4.0,1.75,-4.65),Vector3(4.0,.0,-6.85),54.0);await shot(prefix+"floor_patch_full")
	look(Vector3(3.38,.85,-5.62),Vector3(3.38,.0,-6.45),44.0);await shot(prefix+"p12_p13_contact_detail")
	# Offset the technical top-down target slightly so Godot has a stable up axis.
	look(Vector3(4.0,8.0,-6.5),Vector3(4.01,0.0,-6.5),46.0);await shot(prefix+"floor_patch_topdown",true)
func hide_pods_for_diagnostic() -> Array[Dictionary]:
	var snapshots:Array[Dictionary]=[]
	var pods:Node3D=room.get_node("Pods") as Node3D
	snapshots.append({"node":pods,"visible":pods.visible});pods.visible=false
	snapshots.append({"node":room.standard,"visible":room.standard.visible});room.standard.visible=false
	for item:Dictionary in room.standard_bloom_meshes:
		if is_instance_valid(item.clone):
			snapshots.append({"node":item.clone,"visible":item.clone.visible});item.clone.visible=false
	for proxy in room.screen_proxies.values():
		if is_instance_valid(proxy):
			snapshots.append({"node":proxy,"visible":proxy.visible});proxy.visible=false
	pods_hidden=true
	return snapshots
func restore_pods(snapshots:Array[Dictionary]) -> void:
	for item:Dictionary in snapshots:
		if is_instance_valid(item.node):(item.node as Node3D).visible=bool(item.visible)
	pods_hidden=false
func diagnostic_floor_views(prefix:String) -> void:
	var snapshots:=hide_pods_for_diagnostic()
	look(Vector3(4.0,6.8,-6.5),Vector3(4.01,0.0,-6.5),48.0);await shot(prefix+"floor_patch_unoccluded",true)
	restore_pods(snapshots)
func capture() -> void:
	room=get_parent() as Node3D
	assert(room._r25_assets_available(),"r25 capture requires floor comparison assets")
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
	freeze_overlays();room.set_process(false);room.set_physics_process(false)
	for mode:int in [1,2,3]:
		room.set_r25_mode(mode);hero.set_open_immediate(false);await floor_patch_views("%d_"%mode);await diagnostic_floor_views("%d_"%mode)
		hero.set_open_immediate(true);await follow_view(Vector3(4.2,.05,-5.35));await shot("%d_game_floor_patch_open"%mode)
	room.set_r25_mode(1);hero.set_open_immediate(false);look(Vector3(4.0,1.75,-4.65),Vector3(4.0,.0,-6.85),54.0);await shot("1_restore_floor_patch")
	# Original-color diagnostics separate texture density from the deliberately
	# dim in-game emergency lighting. They do not change any light settings.
	set_base_color(1.0)
	for mode:int in [1,2,3]:
		room.set_r25_mode(mode);hero.set_open_immediate(false)
		look(Vector3(4.0,1.75,-4.65),Vector3(4.0,.0,-6.85),54.0);await shot("%d_base_color_floor_patch"%mode,true)
		var snapshots:=hide_pods_for_diagnostic()
		look(Vector3(4.0,6.8,-6.5),Vector3(4.01,0.0,-6.5),48.0);await shot("%d_base_color_floor_unoccluded"%mode,true)
		restore_pods(snapshots)
	set_base_color(0.0);room.set_r25_mode(3)
	for raw:bool in [true,false]:
		room.set_complete_lightmaps(raw)
		look(Vector3(4.0,1.75,-4.65),Vector3(4.0,.0,-6.85),54.0);await shot("3_"+("raw" if raw else "denoised")+"_floor_patch",true)
	room.set_complete_lightmaps(false)
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
