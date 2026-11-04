extends Node
const OUT := "res://docs/art/experiments/cryo_4f_complete_v3/evidence/"
var level: Node3D
var records: Array = []
func _ready() -> void:call_deferred("run")
func frames(n: int) -> void:
	for i in n:await get_tree().process_frame
func interact() -> void:
	var event := InputEventAction.new();event.action="interact";event.pressed=true;Input.parse_input_event(event)
	event=InputEventAction.new();event.action="interact";event.pressed=false;Input.parse_input_event(event)
func shot(name: String,settle: int=12) -> void:
	level._sync_render_camera();level._sync_bloom_camera();level._sync_paper_hero();level._sync_door_glow()
	await frames(settle);await RenderingServer.frame_post_draw
	var im := get_viewport().get_texture().get_image();assert(im.save_png(OUT+name+".png")==OK)
	var camera := level.get_node("ReviewCamera") as Camera3D
	records.append({"file":name+".png","camera":str(camera.global_transform),"fov":camera.fov,"projection":camera.projection,"raw":level.raw_corridor_light,"door_fraction":level.door_fraction,"portal_view_outside":level.corridor_view,"realtime_lights":level.sample_lights.visible,"fps":Engine.get_frames_per_second()})
	print("F4_SHOT ",name)
func settle_ghosts() -> void:
	for i in 24:level._update_occlusion();await frames(1)
func run() -> void:
	level=get_parent();DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	assert(ResourceLoader.exists(level.FLOOR_ROOT+"strip_irradiance_denoised.exr"),"Final evidence requires whole-floor bake")
	await frames(100);level.finish_exit();level.review_ui.close_dialogue();level.test_mode=true;level.test_input=Vector2.ZERO
	level.teleport_player(Vector3(10.5,.05,-8.2));await frames(120)
	level.info.get_parent().hide()
	await shot("portal_01_idle")
	interact();await frames(45);await shot("portal_02_authenticating")
	await frames(270);await shot("portal_03_open_black")
	interact()
	for i in 90:
		await frames(1)
		if level.fade_rect.color.a>.999:await shot("portal_04_transfer_black",0);break
	for i in 90:
		await frames(1)
		if not level.switching_view:break
	await frames(20);await shot("portal_05_outside")
	interact();await frames(60);await shot("portal_06_inside_restored")
	level.set_process(false);level.set_physics_process(false)
	level.review_ui.hide_interaction_name(level.door_sensor);level.review_ui.hide_interaction_name(level.locked_prompt_owner)
	# Full 4F envelope: labels only belong to this technical overview.
	level.overview_on=true;level.update_follow_camera();await shot("full_floor_overview")
	level.overview_on=false
	var viewpoints := {"sw_room1":Vector3(10.5,.05,-10.7),"sw_middle":Vector3(41.7,.05,-10.7),"sw_inner_gate":Vector3(81.6,.05,-10.7),"sw_second_corridor":Vector3(31.3,.05,-22.6),"sw_foyer":Vector3(-1.2,.05,-16.65),"west_stair_approach":Vector3(-1.2,.05,-35.8),"se_corridor":Vector3(144.7,.05,-10.7),"nw_corridor":Vector3(41.7,.05,-55.2),"ne_corridor":Vector3(144.7,.05,-55.2)}
	for raw in [true,false]:
		level.set_corridor_raw(raw)
		var prefix := "raw" if raw else "denoised"
		for key in viewpoints:
			level.review_teleport(viewpoints[key]);level._sync_paper_hero();await settle_ghosts();await shot(prefix+"_"+key)
	level.set_corridor_raw(false);level.review_teleport(Vector3(41.7,.05,-10.7));await settle_ghosts();await shot("occlusion_on")
	level.room_wall_occlusion_enabled=false;level._update_occlusion();await shot("occlusion_off")
	level.room_wall_occlusion_enabled=true;await settle_ghosts();await shot("occlusion_restored")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
