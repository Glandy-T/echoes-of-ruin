extends Node
const OUT := "res://docs/art/experiments/cryo_4f_facade_v5/evidence/"
var level: Node3D
var records: Array=[]
func _ready() -> void:call_deferred("run")
func frames(n: int) -> void:
	for i in n:await get_tree().process_frame
func interact() -> void:
	var e := InputEventAction.new();e.action="interact";e.pressed=true;Input.parse_input_event(e)
	e=InputEventAction.new();e.action="interact";e.pressed=false;Input.parse_input_event(e)
func shot(name: String) -> void:
	level._sync_render_camera();level._sync_bloom_camera();level._sync_paper_hero();level._sync_door_glow()
	await frames(3);await RenderingServer.frame_post_draw
	assert(get_viewport().get_texture().get_image().save_png(OUT+name+".png")==OK)
	var alphas := {}
	for entry in level.occluders:
		if "Door_D005" in str(entry.mesh.name) or str(entry.mesh.name) in ["Header_D005","Shell_W032","Shell_W033"]:alphas[str(entry.mesh.name)]=entry.get("alpha",1.0)
	records.append({"file":name+".png","position":str(level.player.position),"target":level._interaction_door_target().get("id",""),"main_prompt":level.main_prompt_text,"locked_prompt":level.locked_prompt_visible,"door_fraction":level.door_fraction,"facade_alphas":alphas,"last_interaction":level.last_locked_interaction.duplicate(true)})
	print("FACADE_SHOT ",name)
func run() -> void:
	level=get_parent();await frames(100);level.finish_exit();level.review_ui.close_dialogue()
	level.test_mode=true;level.test_input=Vector2.ZERO;level.info.get_parent().hide()
	for x in [9.15,9.8,10.5,11.4]:
		level.review_teleport(Vector3(x,.05,-10.7));await frames(50);await shot("lateral_"+str(x).replace(".","_"))
	# Physically walk left and right across the doorway's screen projection.
	level.review_teleport(Vector3(9.15,.05,-10.7));await frames(30)
	level.test_input=Vector2(1,0)
	await frames(42);await shot("walk_crossing")
	level.test_input=Vector2.ZERO;await frames(30)
	level.review_teleport(Vector3(10.5,.05,-11.4));await frames(30);await shot("opposite_target")
	interact();await frames(4);await shot("opposite_yellow")
	await frames(100);await shot("opposite_red")
	# Authenticate and leave Room1, then interact with the opposite while main is open.
	level.corridor_view=false;level.teleport_player(Vector3(10.5,.05,-8.2));await frames(40)
	interact();await frames(310);interact();await frames(60)
	level.teleport_player(Vector3(10.5,.05,-11.4));await frames(3);await shot("open_main_opposite_target")
	interact();await frames(4);await shot("open_main_opposite_yellow")
	await frames(100);await shot("open_main_opposite_red")
	level.teleport_player(Vector3(10.5,.05,-10.0));await frames(5)
	if level.door_fraction<.99:interact();await frames(310)
	await shot("main_return_target")
	interact();await frames(60);await shot("returned_inside")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
