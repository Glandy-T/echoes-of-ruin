extends Node

const OUT := "res://docs/art/experiments/cryo_corridor_sample_v1/"
var errors: Array[String] = []
var room: Node3D
var data: Dictionary = {}
var visual := false

func _ready() -> void:
	call_deferred("run")

func frames(count: int) -> void:
	for i in count:await get_tree().physics_frame

func check(ok: bool,message: String) -> void:
	if not ok:errors.append(message)

func shot(name: String) -> void:
	if not visual:return
	await RenderingServer.frame_post_draw
	var im := get_viewport().get_texture().get_image()
	check(im.save_png(OUT+"evidence/"+name+".png")==OK,"Screenshot save failed")

func wait_transition() -> void:
	for i in 180:
		if not room.switching_view:return
		await frames(1)
	check(false,"Transition timed out")

func run() -> void:
	room=get_parent()
	visual=DisplayServer.get_name()!="headless"
	await frames(100)
	room.finish_exit()
	room.review_ui.close_dialogue()
	room.test_mode=true
	room.test_input=Vector2.ZERO
	room.teleport_player(Vector3(10.5,.05,-8.6))
	await frames(120)
	check(room.scan_time==0.0 and room.door_fraction==0.0,"Proximity started authentication without interaction")
	var interact := InputEventAction.new()
	interact.action="interact"
	interact.pressed=true
	Input.parse_input_event(interact)
	await frames(310)
	check(room.door_fraction>.95,"Room 1 door did not open")
	var before := (room.get_node("ReviewCamera") as Camera3D).global_basis.z
	await shot("transition_01_inside")
	room.test_input=Vector2(0,-1)
	for i in 160:
		await frames(1)
		if room.switching_view:break
	check(room.switching_view,"Crossing did not start black transition")
	room.test_input=Vector2.ZERO
	var switched_at_alpha := -1.0
	for i in 90:
		await frames(1)
		if room.corridor_view:
			switched_at_alpha=room.fade_rect.color.a
			await shot("transition_02_black")
			break
	check(switched_at_alpha>.99,"Camera rotated before screen became black")
	await wait_transition()
	await frames(30)
	var after := (room.get_node("ReviewCamera") as Camera3D).global_basis.z
	var a := Vector2(before.x,before.z).normalized()
	var b := Vector2(after.x,after.z).normalized()
	check(a.dot(b)<-.999,"Yaw is not a 180 degree reverse")
	check(room.fade_rect.color.a<.001,"Black overlay remained after transition")
	var ghosts: Array[String] = []
	for entry in room.occluders:
		if entry.active:ghosts.append(str(entry.mesh.name))
	check(not ghosts.is_empty(),"No blocking other-room geometry faded")
	await shot("transition_03_reverse180")
	data['yaw_dot']=a.dot(b)
	data['rotation_black_alpha']=switched_at_alpha
	data['ghosts_outside']=ghosts
	var count_before: int = room.camera_events.size()
	await frames(60)
	check(room.camera_events.size()==count_before,"Idle boundary retriggered transition")
	# Exercise the real physical-key path, not just the verifier's world-space input.
	room.test_mode=false
	var key := InputEventKey.new()
	key.physical_keycode=KEY_D
	key.pressed=true
	var old_x: float = room.player.position.x
	Input.parse_input_event(key)
	await frames(25)
	key=InputEventKey.new()
	key.physical_keycode=KEY_D
	key.pressed=false
	Input.parse_input_event(key)
	var new_x: float = room.player.position.x
	check(new_x<old_x-.2,"Outside D input did not move screen-right after 180 turn")
	data['outside_D_world_delta_x']=new_x-old_x
	room.test_mode=true
	room.teleport_player(Vector3(10.5,.05,-10.1))
	Input.parse_input_event(interact)
	await frames(310)
	room.test_input=Vector2(0,1)
	for i in 180:
		await frames(1)
		if room.switching_view:break
	room.test_input=Vector2.ZERO
	check(room.switching_view,"Return to Room 1 did not transition")
	await wait_transition()
	await frames(35)
	check(not room.corridor_view,"Indoor view not restored")
	for entry in room.occluders:
		check(not entry.active,"Ghost material not restored: "+str(entry.mesh.name))
	check(room.fade_rect.color.a<.001,"Return fade did not finish")
	await shot("transition_04_inside_restored")
	data['result']='PASS' if errors.is_empty() else 'FAIL'
	data['errors']=errors
	data['events']=room.camera_events
	data['r30_mode']=room.r30_mode
	data['collision_bodies']=room.route_bodies.size()
	data['authentication']='proximity stays idle; explicit E starts scan'
	data['portal_black_double_sided']=room.get_node("BlackDoorway").visible
	FileAccess.open(OUT+"camera_validation.json",FileAccess.WRITE).store_string(JSON.stringify(data,"\t"))
	print("CORRIDOR_CAMERA ",JSON.stringify(data))
	get_tree().quit(0 if errors.is_empty() else 1)
