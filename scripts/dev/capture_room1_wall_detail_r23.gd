extends Node

const OUT := "res://docs/art/experiments/room1_wall_detail_r23/evidence/"
var room:Node3D
var camera:Camera3D
var hero:Node3D
var records:Array[Dictionary]=[]
var follow_fov:=0.0

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
	records.append({"file":name+".png","mode":room.r23_mode,"camera":str(camera.global_transform),"fov":camera.fov,"resolution":[image.get_width(),image.get_height()]})

func freeze_screen_overlays() -> void:
	for pod:Node3D in room.room_pods.values():
		var viewport:SubViewport=pod.get("_screen_viewport")
		if viewport:viewport.render_target_update_mode=SubViewport.UPDATE_DISABLED
func set_base_color(enabled:float) -> void:
	for material:ShaderMaterial in room.complete_shell_materials:material.set_shader_parameter("base_color_preview",enabled)
func standard_views(prefix:String) -> void:
	# Normal player camera sees both test panels from the front row.
	room.teleport_player(Vector3(13.6,.05,-4.75));camera.fov=follow_fov
	await shot(prefix+"game_rear_patch_closed")
	# Technical near view: lamp slot down to lower protection strip on same patch.
	look(Vector3(13.6,1.72,-5.55),Vector3(13.6,1.30,-9.28),55.0);await shot(prefix+"rear_patch_full_closed")
	# Wider fixed technical view keeps the lamp slot and both panel top corners in
	# frame.  The pod foreground may obscure part of the lower strip, which is
	# intentional: this checks the ordinary assembled room rather than hiding it.
	look(Vector3(13.6,2.2,-4.5),Vector3(13.6,1.7,-9.28),68.0);await shot(prefix+"rear_patch_whole_closed")
	# Detail isolates the shared vertical seam plus the floor/wall contact.
	look(Vector3(13.6,.48,-6.35),Vector3(13.6,.36,-9.28),52.0);await shot(prefix+"rear_patch_joint_detail_closed")
	set_base_color(1.0)
	look(Vector3(13.6,1.72,-5.55),Vector3(13.6,1.30,-9.28),55.0);await shot(prefix+"rear_patch_base_color")
	set_base_color(0.0)
func capture() -> void:
	room=get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for _i in 120:await get_tree().process_frame
	room.finish_exit();room.review_ui.close_dialogue();room.actor_shadow_on=false;room._sync_actor_shadow()
	for _i in 60:await get_tree().process_frame
	for key:String in ["paper_hero","bloom_paper_hero"]:
		var actor:Sprite3D=room.get(key)
		if actor:actor.visible=false
	room.info.get_parent().hide()
	var ui:Node=room.review_ui
	if ui.get("pause_button"):(ui.get("pause_button") as Control).hide()
	camera=room.get_node("ReviewCamera") as Camera3D;hero=room.room_pods["P12"];follow_fov=camera.fov
	freeze_screen_overlays()
	# The inherited controller must not overwrite technical poses or mutate its
	# live review state between equivalent mode screenshots.
	room.set_process(false);room.set_physics_process(false)
	for mode:int in [1,2,3,4]:
		room.set_r23_mode(mode);hero.set_open_immediate(false);await standard_views("%d_"%mode)
		hero.set_open_immediate(true)
		room.teleport_player(Vector3(13.6,.05,-4.75));camera.fov=follow_fov;await shot("%d_game_rear_patch_open"%mode)
		look(Vector3(13.6,1.72,-5.55),Vector3(13.6,1.30,-9.28),55.0);await shot("%d_rear_patch_full_open"%mode)
		look(Vector3(13.6,2.2,-4.5),Vector3(13.6,1.7,-9.28),68.0);await shot("%d_rear_patch_whole_open"%mode)
	# Restoration check is intentionally reference-only: it confirms exact map
	# restoration without modifying unrelated live material state.
	room.set_r23_mode(1);hero.set_open_immediate(false)
	look(Vector3(13.6,1.72,-5.55),Vector3(13.6,1.30,-9.28),55.0);await shot("1_restore_rear_patch_closed")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
