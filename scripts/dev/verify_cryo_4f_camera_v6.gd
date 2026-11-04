extends Node
const OUT := "res://docs/art/experiments/cryo_4f_camera_compare_v6/"
var level: Node3D
var errors: Array[String]=[]
var report: Dictionary={}
func _ready() -> void:call_deferred("run")
func frames(n: int) -> void:
	for i in n:await get_tree().physics_frame
func check(value: bool,message: String) -> void:
	if not value:errors.append(message)
func interact() -> void:
	var e := InputEventAction.new();e.action="interact";e.pressed=true;Input.parse_input_event(e)
	e=InputEventAction.new();e.action="interact";e.pressed=false;Input.parse_input_event(e)
func reset_reveal() -> void:
	level.reveal_events.clear()
	for section: Dictionary in level.reveal_sections.values():section.latched=false;section.alpha=0.0;section.release_time=0.0
func move(direction: Vector2,n: int) -> void:
	level.test_input=direction;await frames(n);level.test_input=Vector2.ZERO;await frames(15)
func run() -> void:
	level=get_parent();await frames(120);level.finish_exit();level.review_ui.close_dialogue();level.test_mode=true;level.test_input=Vector2.ZERO
	check(level.reveal_sections.size()==32,"Expected 32 complete front room facades")
	check(level.full_floor_colliders.size()==469,"Comparison changed existing collision population")
	level.teleport_player(Vector3(10.5,.05,-8.2));await frames(90)
	var room_camera: Transform3D=level.get_node("ReviewCamera").global_transform
	for i in 5:
		level.set_camera_case(i)
		check(level.get_node("ReviewCamera").global_transform.is_equal_approx(room_camera) and is_equal_approx(level.get_node("ReviewCamera").fov,50.0),"Camera comparison changed Room1 camera")
	check(level.door_fraction==0.0,"Door authenticated without E")
	interact();await frames(310);check(level.door_fraction>.99,"E did not authenticate/open original main door")
	interact();await frames(60);check(level.corridor_view,"Second E did not enter corridor")
	var camera_samples: Array=[]
	for i in 5:
		level.set_camera_case(i)
		for ci in 8:
			var r: Array=level.floor_layout.walk_rects[ci]
			for fraction in [.12,.5,.88]:
				level.review_teleport(Vector3((r[0]+r[2])*.5,.003,4.2-lerpf(r[1],r[3],fraction)))
				var sample: Dictionary=level.camera_report();camera_samples.append(sample)
				check(sample.camera_wall_gap>=.35,"Camera crossed foreground wall")
				check(sample.hero_head_y>=0 and sample.hero_feet_y<=720,"Camera crops character in "+str(sample))
	report.camera_samples=camera_samples
	level.set_camera_case(1);level.wall_override=0;level.reveal_level_index=0
	var trigger_samples: Array=[]
	for mode in 2:
		level.set_trigger_case(mode);reset_reveal()
		level.review_teleport(Vector3(16.0,.05,-10.5));await frames(40)
		check(level.reveal_sections.D005.alpha<.001,"Wall not hidden away from foreground")
		level.review_teleport(Vector3(16.0,.05,-11.4));await frames(40)
		var off_door: float=level.reveal_sections.D005.alpha
		check(off_door>.49 if mode==0 else off_door<.001,"Distance/door-front region rules do not differ")
		level.review_teleport(Vector3(10.5,.05,-11.4));await frames(40)
		check(level.reveal_sections.D005.alpha>.49,"Near door did not reveal full facade section")
		trigger_samples.append({"rule":mode,"off_door_alpha":off_door,"near_door_alpha":level.reveal_sections.D005.alpha})
	report.trigger_samples=trigger_samples
	level.set_trigger_case(0);reset_reveal();level.review_teleport(Vector3(10.5,.05,-10.83));await frames(20)
	for i in 8:
		level.teleport_player(Vector3(10.5,.05,-10.87 if i%2==0 else -10.83));await frames(4)
	check(level.reveal_events.size()==1,"Threshold jitter repeatedly toggled wall")
	level.teleport_player(Vector3(10.5,.05,-10.5));await frames(5)
	check(level.reveal_sections.D005.latched,"Reveal disappeared before release hold")
	await frames(40);check(level.reveal_events.size()==2 and level.reveal_sections.D005.alpha<.001,"Wall failed to fade away after leaving")
	report.distance_jitter_events=level.reveal_events.duplicate(true)
	level.set_trigger_case(1);reset_reveal();level.review_teleport(Vector3(11.68,.05,-11.4));await frames(12)
	for i in 8:
		level.teleport_player(Vector3(11.72 if i%2==0 else 11.68,.05,-11.4));await frames(4)
	check(level.reveal_events.size()==1,"Door-region lateral boundary flickers")
	report.region_jitter_events=level.reveal_events.duplicate(true)
	level.set_trigger_case(0);reset_reveal();level.review_teleport(Vector3(20.96,.05,-11.4));await frames(25)
	for i in 8:
		level.teleport_player(Vector3(21.04 if i%2==0 else 20.96,.05,-11.4));await frames(4)
	check(level.reveal_events.size()==2,"Architectural section boundary repeatedly toggled facade")
	for event: Dictionary in level.reveal_events:check(event.visible,"Facade disappeared during section-boundary jitter")
	report.section_boundary_events=level.reveal_events.duplicate(true)
	level.set_trigger_case(1)
	reset_reveal();level.review_teleport(Vector3(10.5,.05,-10.78));await frames(30)
	check(level.reveal_sections.D005.alpha<.001,"Pre-auth reference should be hidden")
	var portal_count: int=level.portal_events.size()
	interact();await frames(20)
	check(level.reveal_sections.D005.alpha>.49,"Hidden door authentication did not reveal status display")
	await frames(90)
	check(level.last_locked_interaction.get("outcome")=="denied" and level.portal_events.size()==portal_count,"Opposite door interaction bypassed access")
	check(level.review_ui.can_accept_world_interaction(),"Denied authentication showed modal prompt")
	level.wall_override=1;level.review_teleport(Vector3(10.5,.05,-10.7));await frames(40)
	await move(Vector2(0,-1),100)
	check(level.player.position.z> -11.9,"Hidden facade lost normal collision")
	report.hidden_wall_stop=str(level.player.position)
	level.review_teleport(Vector3(82.0,.05,-10.7));await frames(10);await move(Vector2(1,0),100)
	check(level.player.position.x<83.3,"Hidden-room presentation removed inner gate collision")
	report.gate_stop=str(level.player.position)
	level.wall_override=0;level.teleport_player(Vector3(10.5,.05,-10.0));await frames(5)
	if level.door_fraction<.99:interact();await frames(310)
	interact();await frames(60)
	check(not level.corridor_view and level.get_node("ReviewCamera").fov==50.0,"Returning Room1 failed to restore camera")
	for event: Dictionary in level.portal_events:
		if event.event=="transfer_under_black":check(event.alpha>.999,"Transfer before fully black")
	report.portal_events=level.portal_events.duplicate(true)
	report.errors=errors;report.result="PASS" if errors.is_empty() else "FAIL"
	FileAccess.open(OUT+"functional_validation.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("CAMERA_V6_VERIFY ",JSON.stringify({"result":report.result,"errors":errors,"camera_samples":camera_samples.size()}))
	get_tree().quit(0 if errors.is_empty() else 1)
