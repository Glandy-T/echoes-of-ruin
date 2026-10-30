extends Node

const OUT := "res://docs/art/experiments/room1_pixel_unify_r22/evidence/"
var room:Node3D
var camera:Camera3D
var hero:Node3D
var records:Array=[]
var follow_fov:=0.0
var screen_overlays_frozen:=false

func _ready() -> void:call_deferred("capture")
func look(position:Vector3,target:Vector3,fov:float) -> void:
	camera.global_position=position
	camera.look_at(target,Vector3.UP)
	camera.fov=fov
func shot(name:String) -> void:
	room._sync_render_camera();room._sync_bloom_camera();room._sync_standard_visuals()
	room._sync_complete_room_pose();room._sync_complete_screen_sources();room._sync_door_glow()
	for _i in 12:await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image:=get_viewport().get_texture().get_image()
	assert(image.save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","mode":room.r22_mode,"p12_pose":hero.get_state_name(),"camera":str(camera.global_transform),"fov":camera.fov,"resolution":[image.get_width(),image.get_height()],"screen_overlays_frozen":screen_overlays_frozen})
	print("R22_SHOT ",name)
func follow_view(point:Vector3) -> void:
	room.teleport_player(point)
	camera.fov=follow_fov
	await get_tree().process_frame
func front_wall_views(prefix:String) -> void:
	var front:MeshInstance3D=room.get_node("Shell").find_child("Wall_front",true,false)
	var old_visible:=front.visible;var old_shadow:=front.cast_shadow
	front.visible=true;front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for view:Array in [["corner_front_left",Vector3(2.5,1.9,-3.2),Vector3(.2,1.45,-.25),70.0],["corner_front_right",Vector3(18.5,1.9,-3.2),Vector3(20.8,1.45,-.25),70.0],["front_wall_lamp",Vector3(10.5,2.0,-5.7),Vector3(10.5,1.6,-.2),70.0]]:
		look(view[1],view[2],view[3]);await shot(prefix+view[0])
	front.visible=old_visible;front.cast_shadow=old_shadow
func set_base_color_preview(enabled:float) -> void:
	for material:ShaderMaterial in room.complete_shell_materials:
		material.set_shader_parameter("base_color_preview",enabled)
func raw_denoised_diagnostics() -> void:
	# The r19 GI endpoints are intentionally reused. These screenshots expose
	# their raw/denoised display behavior without claiming a new bake.
	for raw:bool in [true,false]:
		room.set_complete_lightmaps(raw)
		var label:="raw" if raw else "denoised"
		hero.set_open_immediate(true)
		look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44);await shot("2_"+label+"_p12_open")
		hero.set_open_immediate(false)
		look(Vector3(2.5,1.9,-6.2),Vector3(.2,1.45,-9.25),60);await shot("2_"+label+"_corner_rear_left")
	room.set_complete_lightmaps(false)
func base_color_diagnostics() -> void:
	set_base_color_preview(1.0)
	hero.set_open_immediate(false)
	look(Vector3(1.8,1.75,-5.2),Vector3(.2,1.55,-7.1),57);await shot("2_base_color_left_wall")
	var front:MeshInstance3D=room.get_node("Shell").find_child("Wall_front",true,false)
	var old_visible:=front.visible;var old_shadow:=front.cast_shadow
	front.visible=true;front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	look(Vector3(10.5,2.0,-5.7),Vector3(10.5,1.6,-.2),70);await shot("2_base_color_front_wall")
	front.visible=old_visible;front.cast_shadow=old_shadow
	look(Vector3(10.5,10,2.5),Vector3(10.5,.05,-4.75),80);await shot("2_base_color_floor")
	set_base_color_preview(0.0)

func freeze_screen_overlays() -> void:
	# Each pod renders its static labels through a tiny UPDATE_ALWAYS viewport.
	# The content is unchanged, but asynchronous redraw can move a few antialiased
	# edge pixels between otherwise identical screenshots.  Freeze only these
	# capture-time label viewports after the long startup settle; gameplay/runtime
	# behavior is untouched and exact A/B/A readback becomes meaningful.
	for pod:Node3D in room.room_pods.values():
		var screen_viewport:SubViewport=pod.get("_screen_viewport")
		if screen_viewport:screen_viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
	screen_overlays_frozen=true
func full_closed_set(prefix:String,with_pod_coverage:bool) -> void:
	for row:Array in [["front",-4.75], ["back",-8.0]]:
		for column:Array in [["left",3.525], ["middle",10.5], ["right",17.475]]:
			await follow_view(Vector3(column[1],.05,row[1]))
			await shot(prefix+"game_"+str(row[0])+"_"+str(column[0])+"_closed")
	look(Vector3(10.5,13,6.5),Vector3(10.5,0,-4.75),78);await shot(prefix+"whole_room_closed")
	look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44);await shot(prefix+"p12_oblique_closed")
	for view:Array in [["corner_rear_left",Vector3(2.5,1.9,-6.2),Vector3(.2,1.45,-9.25),60.0],["corner_rear_right",Vector3(18.5,1.9,-6.2),Vector3(20.8,1.45,-9.25),60.0],["door_header",Vector3(10.5,2.55,-4.3),Vector3(10.5,2.1,-9.25),60.0]]:
		look(view[1],view[2],view[3]);await shot(prefix+view[0])
	await front_wall_views(prefix)
	look(Vector3(10.5,10,2.5),Vector3(10.5,.05,-4.75),80);await shot(prefix+"floor_contacts")
	if with_pod_coverage:
		for record:Dictionary in room.room_pod_records:
			var pod:Node3D=room.room_pods[str(record.id)]
			look(pod.to_global(Vector3(-1.0,1.4,2.9)),pod.to_global(Vector3(0,.35,0)),48)
			await shot(prefix+"pod_"+str(record.id))
func capture() -> void:
	room=get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	# Let the inherited subviewports, shadow sources and opening-state setup settle
	# before freezing scripted room movement.  This keeps the baseline A capture
	# from being the first-frame transient of the review scene.
	for _i in 120:await get_tree().process_frame
	room.finish_exit();room.review_ui.close_dialogue();room.actor_shadow_on=false;room._sync_actor_shadow()
	for _i in 120:await get_tree().process_frame
	for key in ["paper_hero","bloom_paper_hero"]:
		var actor:Sprite3D=room.get(key)
		if actor:actor.visible=false
	room.info.get_parent().hide()
	var ui:Node=room.review_ui
	if ui.get("pause_button"):(ui.get("pause_button") as Control).hide()
	camera=room.get_node("ReviewCamera") as Camera3D;hero=room.room_pods["P12"];follow_fov=camera.fov
	freeze_screen_overlays()
	room.set_process(false);room.set_physics_process(false)
	for mode:int in [1,2]:
		room.set_r22_mode(mode);hero.set_open_immediate(false)
		await full_closed_set("%d_"%mode,mode==2)
		if mode==1:
			look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44);await shot("1_repeat_p12_oblique_closed")
		hero.set_open_immediate(true)
		await follow_view(Vector3(3.525,.05,-4.75));await shot("%d_game_front_left_open"%mode)
		look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44);await shot("%d_p12_oblique_open"%mode)
	room.set_r22_mode(1);hero.set_open_immediate(false)
	look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44);await shot("1_restore_p12_closed")
	# Capture the material-switch restoration before raw/denoised diagnostics;
	# those deliberately reload existing GI endpoint textures for inspection.
	room.set_r22_mode(2)
	await raw_denoised_diagnostics()
	await base_color_diagnostics()
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
