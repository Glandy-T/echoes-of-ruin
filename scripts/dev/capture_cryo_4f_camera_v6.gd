extends Node
const OUT := "res://docs/art/experiments/cryo_4f_camera_compare_v6/evidence/"
var level: Node3D
var records: Array=[]
var motion_records: Dictionary={}
var metric_records: Array=[]
func _ready() -> void:call_deferred("run")
func frames(n: int) -> void:
	for i in n:await get_tree().process_frame
func sync() -> void:
	level._sync_render_camera();level._sync_bloom_camera();level._sync_paper_hero();level._sync_door_glow()
func shot(name: String,settle: int=3) -> void:
	sync();await frames(settle);await RenderingServer.frame_post_draw
	assert(get_viewport().get_texture().get_image().save_png(OUT+name+".png")==OK)
	var record: Dictionary=level.camera_report();record.merge({"file":name+".png","trigger":level.trigger_case,"reveal_level":level.REVEAL_LEVELS[level.reveal_level_index],"door_alpha":level.reveal_sections.D005.alpha,"position_player":str(level.player.position),"fps":Engine.get_frames_per_second()})
	records.append(record);print("CAMERA_V6_SHOT ",name)
func interact() -> void:
	var e := InputEventAction.new();e.action="interact";e.pressed=true;Input.parse_input_event(e)
	e=InputEventAction.new();e.action="interact";e.pressed=false;Input.parse_input_event(e)
func motion(name: String,mode: int,lateral: bool) -> void:
	level.set_trigger_case(mode);level.wall_override=0;level.reveal_level_index=0
	level.review_teleport(Vector3(10.5,.05,-11.4 if lateral else -10.2));await frames(50)
	var samples: Array=[]
	var start_time: float=level.comparison_time
	for i in 144:
		if lateral:level.test_input=Vector2(1,0) if i<90 else Vector2.ZERO
		else:level.test_input=Vector2(0,-1) if i<40 else (Vector2(0,1) if i>=75 and i<120 else Vector2.ZERO)
		await frames(1)
		if i%6==0:
			var filename := "motion_%s_%03d"%[name,i]
			await shot(filename,0)
			samples.append({"frame":i,"time":level.comparison_time-start_time,"alpha":level.reveal_sections.D005.alpha,"latched":level.reveal_sections.D005.latched,"position":str(level.player.position),"file":filename+".png"})
	level.test_input=Vector2.ZERO;await frames(20);motion_records[name]=samples
func metric_pair(prefix: String) -> void:
	level.paper_time=0.0;level.paper_hero.frame=0;level.paper_hero.show();await shot(prefix+"_hero",2)
	level.paper_hero.hide();await shot(prefix+"_empty",2);level.paper_hero.show()
func run() -> void:
	level=get_parent();await frames(120);level.finish_exit();level.review_ui.close_dialogue();level.test_mode=true;level.test_input=Vector2.ZERO;level.info.get_parent().hide()
	for i in 5:
		level.set_camera_case(i);level.set_trigger_case(0);level.wall_override=0;level.reveal_level_index=0
		level.review_teleport(Vector3(16.0,.05,-10.7));await frames(45);await shot("camera_"+level.CAMERA_CASES[i].id+"_hidden")
		level.review_teleport(Vector3(10.5,.05,-11.4));await frames(45);await shot("camera_"+level.CAMERA_CASES[i].id+"_half")
		level.reveal_level_index=1;await frames(35);await shot("camera_"+level.CAMERA_CASES[i].id+"_solid")
	level.set_camera_case(1);level.reveal_level_index=0
	for mode in 2:
		level.set_trigger_case(mode)
		for point in [Vector3(16.0,.05,-10.5),Vector3(16.0,.05,-11.4),Vector3(10.5,.05,-11.4)]:
			level.review_teleport(point);await frames(50)
			await shot("trigger_%d_%s"%[mode,"far" if point.z> -11 else ("near_door" if point.x<11 else "near_wall")])
	for mode in 2:
		await motion("%s_approach"%("distance" if mode==0 else "region"),mode,false)
		await motion("%s_lateral"%("distance" if mode==0 else "region"),mode,true)
	# Fixed-pose hero/empty pairs measure actual character contrast loss.
	level.review_teleport(Vector3(10.5,.003,-11.4));await frames(30)
	level.set_process(false);level.set_physics_process(false)
	level.review_ui.hide_interaction_name(level.door_sensor);level.review_ui.hide_interaction_name(level.locked_prompt_owner)
	for i in 5:
		level.set_camera_case(i)
		for cap in [-1,0,1]:
			level.wall_override=1 if cap<0 else 2;level.reveal_level_index=maxi(cap,0)
			for step in 40:level._update_reveal_states(1.0/60.0);level._apply_comparison_visibility()
			var prefix := "metric_%s_%s"%[level.CAMERA_CASES[i].id,"hidden" if cap<0 else ("half" if cap==0 else "solid")]
			await metric_pair(prefix)
			var r: Dictionary=level.camera_report();r["prefix"]=prefix;metric_records.append(r)
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	FileAccess.open(OUT+"motion_record.json",FileAccess.WRITE).store_string(JSON.stringify(motion_records,"\t"))
	FileAccess.open(OUT+"metric_record.json",FileAccess.WRITE).store_string(JSON.stringify(metric_records,"\t"))
	get_tree().quit()
