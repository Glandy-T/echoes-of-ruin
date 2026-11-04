extends Node
const OUT := "res://docs/art/experiments/cryo_4f_feedback_v4/evidence/"
var level: Node3D
var record: Dictionary = {}
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
	print("FEEDBACK_SHOT ",name)
func door_alphas() -> Dictionary:
	var result := {}
	for e in level.occluders:
		if "Door_D005" in str(e.mesh.name):result[str(e.mesh.name)]=e.get("alpha",1.0)
	return result
func run() -> void:
	level=get_parent();await frames(100);level.finish_exit();level.review_ui.close_dialogue()
	level.test_mode=true;level.test_input=Vector2.ZERO;level.info.get_parent().hide()
	level.review_teleport(Vector3(41.7,.05,-10.7));await frames(80);await shot("after_occlusion_on")
	level.room_wall_occlusion_enabled=false;level._update_occlusion();await shot("opaque_reference")
	level.room_wall_occlusion_enabled=true;await frames(80);await shot("after_occlusion_restored")
	level.review_teleport(Vector3(31.3,.05,-22.6));await frames(80);await shot("after_sw_second_corridor")
	# Opposite room D005: same horizontal camera, approach rather than teleporting through it.
	level.review_teleport(Vector3(10.5,.05,-10.7));await frames(80)
	record['door_alpha_far']=door_alphas();await shot("opposite_far")
	level.test_input=Vector2(0,-1);await frames(70);level.test_input=Vector2.ZERO;await frames(30)
	record['door_alpha_near']=door_alphas();await shot("opposite_near_idle")
	interact();await frames(3);await shot("opposite_yellow_on")
	await frames(17);await shot("opposite_yellow_dim")
	await frames(80);await shot("opposite_red_denied")
	record['door_state']=level.locked_door_feedback["D005"].state
	record['history']=level.locked_door_feedback["D005"].history.duplicate()
	record['no_modal_text']=level.review_ui.can_accept_world_interaction()
	await frames(100);await shot("opposite_idle_restored")
	# Step sideways: a nearby gate outside the body sightline stays fully opaque.
	level.review_teleport(Vector3(82.4,.05,-10.7));await frames(80)
	# This perpendicular gate is edge-on in the fixed gameplay camera. Inspect
	# its real face with a temporary oblique technical camera, never save it.
	level.set_process(false);level.set_physics_process(false)
	var camera := level.get_node("ReviewCamera") as Camera3D
	camera.position=Vector3(78.0,2.2,-14.0);camera.look_at(Vector3(83.4,1.2,-10.7),Vector3.UP)
	await shot("side_gate_idle")
	level._start_locked_authentication("D017")
	level._update_locked_feedback(.08);await shot("side_gate_yellow")
	level._update_locked_feedback(1.5);await shot("side_gate_red")
	record['wall_opacity']=level._occlusion_opacity()
	FileAccess.open(OUT+"verification.json",FileAccess.WRITE).store_string(JSON.stringify(record,"\t"))
	get_tree().quit()
