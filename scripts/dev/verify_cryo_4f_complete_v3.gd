extends Node
const OUT := "res://docs/art/experiments/cryo_4f_complete_v3/"
var level: Node3D
var errors: Array[String] = []
var result: Dictionary = {}
func _ready() -> void:call_deferred("run")
func frames(n: int) -> void:
	for i in n:await get_tree().physics_frame
func check(ok: bool,message: String) -> void:
	if not ok:errors.append(message)
func interact() -> void:
	var event := InputEventAction.new();event.action="interact";event.pressed=true;Input.parse_input_event(event)
	event=InputEventAction.new();event.action="interact";event.pressed=false;Input.parse_input_event(event)
func movement(direction: Vector2,count: int) -> void:
	level.test_input=direction;await frames(count);level.test_input=Vector2.ZERO;await frames(15)
func run() -> void:
	level=get_parent();await frames(100)
	level.finish_exit();level.review_ui.close_dialogue();level.test_mode=true;level.test_input=Vector2.ZERO
	check(level.floor_layout.room_count==48,"Not all 48 room envelopes retained")
	check(level.floor_layout.other_room_pods==0 and level.room_pods.size()==20,"Unexpected pod population outside Room1")
	check(level.corridor_sample.find_children("*pod*","Node",true,false).is_empty(),"Extra pod node in floor exterior model")
	level.teleport_player(Vector3(10.5,.05,-8.2));await frames(120)
	check(level.scan_time==0.0 and level.door_fraction==0.0,"Door auto-authenticated without E")
	interact();await frames(310)
	check(level.door_fraction>.99,"First E did not authenticate and open door")
	await movement(Vector2(0,-1),150)
	check(not level.corridor_view and level.player.position.z> -9.25,"Walking through black portal bypassed E")
	check(level.portal_events.is_empty(),"Walking unexpectedly triggered portal")
	result['inside_walk_stop']=str(level.player.position)
	interact();await frames(60)
	check(level.corridor_view and level.player.position.z< -10.0,"Second E did not enter corridor")
	await movement(Vector2(0,1),150)
	check(level.corridor_view and level.player.position.z< -9.4,"Outside walking bypassed return interaction")
	result['outside_walk_stop']=str(level.player.position)
	interact();await frames(60)
	check(not level.corridor_view and level.player.position.z> -9.25,"E on outside portal did not return")
	for event in level.portal_events:
		if event.event=="transfer_under_black":check(event.alpha>.99,"Portal teleported before full black")
	check(level.get_node("BlackDoorway").visible,"Portal lost opaque black cover")
	result['portal_events']=level.portal_events.duplicate(true)
	# Walk the new full corridor extent, not the old x<=21 route crop.
	level.review_teleport(Vector3(10.5,.05,-10.7));await frames(30)
	level.test_input=Vector2(1,0)
	for i in 2500:
		await frames(1)
		if level.player.position.x>81.0:break
	level.test_input=Vector2.ZERO;await frames(20)
	check(level.player.position.x>80 and absf(level.player.position.y)<.1,"Could not walk full first SW corridor")
	await movement(Vector2(1,0),150)
	check(level.player.position.x<83.5,"Controlled inner gate failed to block access")
	result['inner_gate_stop']=str(level.player.position)
	interact();await frames(2)
	check(not level.last_locked_interaction.is_empty(),"Inner gate has no interaction response")
	result['inner_gate_response']=level.last_locked_interaction.duplicate(true)
	level.review_ui.close_dialogue()
	# Foyer joins the second corridor without crossing a locked room.
	level.review_teleport(Vector3(-1.2,.05,-10.7));await frames(10)
	await movement(Vector2(0,-1),365)
	level.test_input=Vector2.ZERO
	check(level.player.position.z< -22 and absf(level.player.position.y)<.1,"Foyer-to-second-corridor route failed")
	level.review_teleport(Vector3(-1.2,.05,-22.6));await frames(5)
	await movement(Vector2(1,0),365)
	check(level.player.position.x>10 and absf(level.player.position.y)<.1,"Second SW corridor entrance blocked")
	result['second_corridor_end']=str(level.player.position)
	# A neighboring room stays closed and rejects E.
	level.review_teleport(Vector3(10.5,.05,-10.7));await frames(10)
	await movement(Vector2(0,-1),100)
	check(level.player.position.z> -12.0,"Neighbor room collision allowed entry")
	interact();await frames(2)
	check(level.last_locked_interaction.get("outcome")=="denied","Neighbor room did not deny access")
	result['neighbor_room_response']=level.last_locked_interaction.duplicate(true)
	level.review_ui.close_dialogue()
	# All eight corridor centerlines have real floor, not just an overview mesh.
	var rays: Array = []
	for r in level.floor_layout.walk_rects:
		var point := Vector3((r[0]+r[2])*.5,.6,4.2-(r[1]+r[3])*.5)
		var query := PhysicsRayQueryParameters3D.create(point,point-Vector3(0,1,0),1)
		var hit: Dictionary=level.get_world_3d().direct_space_state.intersect_ray(query)
		check(not hit.is_empty(),"No floor under walk rectangle "+str(r))
		rays.append({"point":str(point),"collider":str(hit.collider.name) if not hit.is_empty() else ""})
	result['walk_floor_rays']=rays
	result['full_floor_collision_bodies']=level.full_floor_colliders.size()
	result['room_count']=level.floor_layout.room_count
	result['other_room_pods']=0
	result['bake_available']=ResourceLoader.exists(level.FLOOR_ROOT+"strip_irradiance_denoised.exr")
	check(not level.sample_lights.visible,"Temporary realtime lamps enabled")
	result['errors']=errors;result['result']='PASS' if errors.is_empty() else 'FAIL'
	FileAccess.open(OUT+"functional_validation.json",FileAccess.WRITE).store_string(JSON.stringify(result,"\t"))
	print("F4_FUNCTIONAL ",JSON.stringify(result))
	get_tree().quit(0 if errors.is_empty() else 1)
