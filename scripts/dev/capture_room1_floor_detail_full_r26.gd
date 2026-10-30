extends Node

const OUT := "res://docs/art/experiments/room1_floor_detail_full_r26/evidence/"
# At 16:9 with KEEP_WIDTH, 15m only covered about 13.35m across the 20.6m
# floor. 28m is deliberately conservative and keeps every interior edge in
# frame without changing the review FOV.
const TOPDOWN_POSITION := Vector3(10.5,28.0,-4.75)
const TOPDOWN_TARGET := Vector3(10.5,0.0,-4.74)
const TOPDOWN_FOV := 48.0
const FLOOR_BOUNDS := Rect2(0.2,-9.3,20.6,9.1)
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
func shot(name:String,diagnostic:bool=false,coverage:Array=[],force_topdown:bool=false) -> void:
	room._sync_render_camera();room._sync_bloom_camera();room._sync_standard_visuals()
	room._sync_complete_room_pose();room._sync_complete_screen_sources();room._sync_door_glow()
	# The inherited review scene can synchronize its render camera during a
	# visual refresh. Re-apply this diagnostic camera after that refresh so the
	# recorded source and the actual SubViewport camera are the same one.
	if force_topdown:
		look(TOPDOWN_POSITION,TOPDOWN_TARGET,TOPDOWN_FOV)
		room._sync_render_camera();room._sync_bloom_camera()
	for _i in 12:await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image:=get_viewport().get_texture().get_image()
	assert(image.save_png(OUT+name+".png")==OK)
	var record:Dictionary={"file":name+".png","mode":room.r26_mode,"p12_pose":hero.get_state_name(),"camera":str(camera.global_transform),"fov":camera.fov,"resolution":[image.get_width(),image.get_height()],"overlays_frozen":overlays_frozen,"pods_hidden":pods_hidden,"diagnostic":diagnostic,"coverage":coverage}
	if name.ends_with("floor_topdown_unoccluded") or name=="2_base_color_floor_topdown":
		var horizontal_span:=2.0*TOPDOWN_POSITION.y*tan(deg_to_rad(TOPDOWN_FOV*.5))
		var vertical_span:=horizontal_span/(float(image.get_width())/float(image.get_height()))
		record["topdown_position"]=[TOPDOWN_POSITION.x,TOPDOWN_POSITION.y,TOPDOWN_POSITION.z]
		record["topdown_target"]=[TOPDOWN_TARGET.x,TOPDOWN_TARGET.y,TOPDOWN_TARGET.z]
		record["keep_width"]=camera.keep_aspect==Camera3D.KEEP_WIDTH
		record["projected_bounds_m"]=[TOPDOWN_POSITION.x-horizontal_span*.5,TOPDOWN_POSITION.x+horizontal_span*.5,TOPDOWN_POSITION.z-vertical_span*.5,TOPDOWN_POSITION.z+vertical_span*.5]
		record["required_floor_bounds_m"]=[FLOOR_BOUNDS.position.x,FLOOR_BOUNDS.end.x,FLOOR_BOUNDS.position.y,FLOOR_BOUNDS.end.y]
	for index:int in range(records.size()-1,-1,-1):
		if str(records[index].get("file",""))==str(record["file"]):records.remove_at(index)
	records.append(record)
	print("R26_SHOT ",name)
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
func normal_game_views(prefix:String) -> void:
	for entry:Dictionary in [
		{"name":"game_front_left","pos":Vector3(3.0,.05,-3.8),"ids":["P01","P02","P11","P12"]},
		{"name":"game_front_middle","pos":Vector3(8.2,.05,-3.8),"ids":["P04","P05","P14","P15"]},
		{"name":"game_front_right","pos":Vector3(14.8,.05,-3.8),"ids":["P08","P09","P18","P19"]},
		{"name":"game_back_left","pos":Vector3(3.0,.05,-7.8),"ids":["P01","P02","P11","P12"]},
		{"name":"game_back_middle","pos":Vector3(8.2,.05,-7.8),"ids":["P04","P05","P14","P15"]},
		{"name":"game_back_right","pos":Vector3(14.8,.05,-7.8),"ids":["P08","P09","P18","P19"]}]:
		await follow_view(entry.pos);await shot(prefix+str(entry.name),false,entry.ids)
func corner_views(prefix:String) -> void:
	for entry:Dictionary in [
		{"name":"corner_front_left","pos":Vector3(.7,1.1,-1.4),"target":Vector3(.25,.02,-.25),"ids":["P01","P11"]},
		{"name":"corner_front_right","pos":Vector3(20.25,1.1,-1.4),"target":Vector3(20.75,.02,-.25),"ids":["P10","P20"]},
		{"name":"corner_rear_left","pos":Vector3(.7,1.1,-8.3),"target":Vector3(.25,.02,-9.25),"ids":["P01","P11"]},
		{"name":"corner_rear_right","pos":Vector3(20.25,1.1,-8.3),"target":Vector3(20.75,.02,-9.25),"ids":["P10","P20"]}]:
		look(entry.pos,entry.target,55.0);await shot(prefix+str(entry.name),false,entry.ids)
func pod_contact_views(prefix:String) -> void:
	for id:String in room.room_pods:
		var pod:Node3D=room.room_pods[id]
		var target:=pod.global_position+Vector3(0,0.02,0)
		# The room keeps all pods aligned with its front/back axis; the alternating
		# lateral offset exposes a side contact without crossing a wall.
		var side:= -1.0 if target.x<8.2 else 1.0
		look(target+Vector3(side*1.25,0.7,1.25),target,46.0)
		await shot(prefix+"pod_contact_"+id,false,[id])
func leak_views(prefix:String) -> void:
	# These positions target the four actual residual-difference centroids in
	# the approved r26 map, rather than filling the frame with the pod shell.
	for entry:Dictionary in [
		{"id":"P03","target":Vector3(5.858,.02,-.767),"pos":Vector3(6.658,1.2,-.517)},
		{"id":"P06","target":Vector3(11.692,.02,-.769),"pos":Vector3(10.892,1.2,-.519)},
		{"id":"P13","target":Vector3(5.844,.02,-8.674),"pos":Vector3(6.644,1.2,-8.924)},
		{"id":"P18","target":Vector3(15.199,.02,-8.719),"pos":Vector3(14.399,1.2,-8.969)}]:
		look(entry.pos,entry.target,55.0)
		await shot(prefix+"leak_"+str(entry.id),false,[str(entry.id)])
		records[-1]["leak_target"]=[entry.target.x,entry.target.y,entry.target.z]
		records[-1]["leak_camera_position"]=[entry.pos.x,entry.pos.y,entry.pos.z]
func diagnostic_topdown(prefix:String) -> void:
	var snapshots:=hide_pods_for_diagnostic()
	# Center the real 20.6m x 9.1m floor. The minute Z tilt avoids look_at's
	# vertical up-axis ambiguity while keeping the wide screen axis along X.
	look(TOPDOWN_POSITION,TOPDOWN_TARGET,TOPDOWN_FOV)
	await shot(prefix+"floor_topdown_unoccluded",true,room.room_pods.keys(),true)
	restore_pods(snapshots)
func capture_mode(prefix:String) -> void:
	await normal_game_views(prefix)
	await corner_views(prefix)
	await pod_contact_views(prefix)
	await leak_views(prefix)
	await diagnostic_topdown(prefix)
func capture() -> void:
	room=get_parent() as Node3D
	assert(room._r26_assets_available(),"r26 capture requires full-floor asset")
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
	for mode:int in [1,2]:
		room.set_r26_mode(mode);hero.set_open_immediate(false);await capture_mode("%d_"%mode)
		await follow_view(Vector3(4.2,.05,-5.35));await shot("%d_game_floor_patch_closed"%mode,false,["P12","P13"])
		hero.set_open_immediate(true);await follow_view(Vector3(4.2,.05,-5.35));await shot("%d_game_floor_patch_open"%mode,false,["P12","P13"])
	room.set_r26_mode(1);hero.set_open_immediate(false);await follow_view(Vector3(4.2,.05,-5.35));await shot("1_restore_game_floor_patch",false,["P12","P13"])
	room.set_r26_mode(2);set_base_color(1.0)
	var base_color_hidden:=hide_pods_for_diagnostic()
	look(TOPDOWN_POSITION,TOPDOWN_TARGET,TOPDOWN_FOV);await shot("2_base_color_floor_topdown",true,room.room_pods.keys(),true)
	restore_pods(base_color_hidden)
	set_base_color(0.0)
	for raw:bool in [true,false]:
		room.set_complete_lightmaps(raw)
		look(Vector3(4.0,1.75,-4.65),Vector3(4.0,.0,-6.85),54.0)
		await shot("2_"+("raw" if raw else "denoised")+"_floor_patch",true,["P12","P13"])
	room.set_complete_lightmaps(false)
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
