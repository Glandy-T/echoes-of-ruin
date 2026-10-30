extends Node

const OUT := "res://docs/art/experiments/room1_pixel_cluster_r21/evidence/"
var room: Node3D
var camera: Camera3D
var pod: Node3D
var records: Array = []
var follow_fov := 0.0

func _ready() -> void: call_deferred("capture")
func look(position: Vector3, target: Vector3, fov: float) -> void:
	camera.global_position=position
	camera.look_at(target,Vector3.UP)
	camera.fov=fov
func shot(name: String) -> void:
	room._sync_render_camera()
	room._sync_bloom_camera()
	room._sync_standard_visuals()
	room._sync_complete_room_pose()
	room._sync_complete_screen_sources()
	room._sync_door_glow()
	for _i in 12: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image:=get_viewport().get_texture().get_image()
	assert(image.save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","mode":room.cluster_mode,"p12_pose":pod.get_state_name(),"camera":str(camera.global_transform),"fov":camera.fov,"resolution":[image.get_width(),image.get_height()]})
	print("R21_SHOT ",name)
func follow_view(point: Vector3) -> void:
	room.teleport_player(point)
	# Processing is deliberately frozen below so a previous technical lens cannot
	# leak into a gameplay shot. teleport_player has already refreshed follow pose.
	camera.fov=follow_fov
	await get_tree().process_frame
func set_base_color_preview(enabled: float) -> void:
	for material:ShaderMaterial in room.complete_shell_materials:
		material.set_shader_parameter("base_color_preview",enabled)
func capture() -> void:
	room=get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for _i in 20: await get_tree().process_frame
	room.finish_exit()
	room.review_ui.close_dialogue()
	room.actor_shadow_on=false
	room._sync_actor_shadow()
	for key in ["paper_hero","bloom_paper_hero"]:
		var actor:Sprite3D=room.get(key)
		if actor:actor.visible=false
	room.info.get_parent().hide()
	var ui:Node=room.review_ui
	if ui.get("pause_button"):(ui.get("pause_button") as Control).hide()
	camera=room.get_node("ReviewCamera") as Camera3D
	pod=room.room_pods["P12"]
	follow_fov=camera.fov
	room.set_process(false)
	room.set_physics_process(false)
	for mode in [1,2,3]:
		room.set_cluster_mode(mode)
		for opened in [false,true]:
			pod.set_open_immediate(opened)
			var pose:="open" if opened else "closed"
			await follow_view(Vector3(3.525,.05,-4.75))
			await shot("%s_gameplay_distance_%s"%[mode,pose])
			await follow_view(Vector3(1.8,.05,-6.9))
			await shot("%s_left_distance_%s"%[mode,pose])
			look(Vector3(1.78,1.8,-4.45),Vector3(3.65,.43,-7.65),44)
			await shot("%s_p12_%s"%[mode,pose])
			look(Vector3(1.8,1.75,-5.2),Vector3(.2,1.55,-7.1),57)
			await shot("%s_left_bay_%s"%[mode,pose])
	# Diagnostic images still use r19's original shader. They only activate its
	# existing base-color preview, with no altered light or post-process.
	for mode in [2,3]:
		room.set_cluster_mode(mode)
		pod.set_open_immediate(false)
		set_base_color_preview(1.0)
		look(Vector3(1.8,1.75,-5.2),Vector3(.2,1.55,-7.1),57)
		await shot("%s_left_bay_base_color"%mode)
		set_base_color_preview(0.0)
	room.set_cluster_mode(1)
	pod.set_open_immediate(false)
	look(Vector3(1.78,1.8,-4.45),Vector3(3.65,.43,-7.65),44)
	await shot("1_restore_p12_closed")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
