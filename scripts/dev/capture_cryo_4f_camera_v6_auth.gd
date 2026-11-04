extends Node
const OUT := "res://docs/art/experiments/cryo_4f_camera_compare_v6/evidence/"
var level: Node3D
var records: Array=[]
func _ready() -> void:call_deferred("run")
func frames(n: int) -> void:
	for i in n:await get_tree().process_frame
func interact() -> void:
	var e := InputEventAction.new();e.action="interact";e.pressed=true;Input.parse_input_event(e)
	e=InputEventAction.new();e.action="interact";e.pressed=false;Input.parse_input_event(e)
func shot(name: String,settle: int=3) -> void:
	level._sync_render_camera();level._sync_bloom_camera();level._sync_paper_hero();level._sync_door_glow()
	await frames(settle);await RenderingServer.frame_post_draw
	assert(get_viewport().get_texture().get_image().save_png(OUT+name+".png")==OK)
	var record: Dictionary=level.camera_report()
	var window: MeshInstance3D=level.reveal_sections.D005.state_window
	var point: Vector2=level.get_node("ReviewCamera").unproject_position(window.global_position)
	record.merge({"file":name+".png","door_alpha":level.reveal_sections.D005.alpha,"state":level.locked_door_feedback.D005.state,"status_x":point.x,"status_y":point.y,"main_fraction":level.door_fraction,"outside":level.corridor_view,"black_alpha":level.fade_rect.color.a,"no_modal":level.review_ui.can_accept_world_interaction()})
	records.append(record);print("CAMERA_V6_AUTH ",name)
func run() -> void:
	level=get_parent();await frames(120);level.finish_exit();level.review_ui.close_dialogue();level.test_mode=true;level.test_input=Vector2.ZERO;level.info.get_parent().hide()
	level.set_camera_case(1);level.set_trigger_case(1);level.reveal_level_index=0
	level.review_teleport(Vector3(10.5,.05,-10.78));await frames(40);await shot("auth_hidden_before")
	interact();await frames(34);await shot("auth_yellow")
	await frames(65);await shot("auth_red")
	level.corridor_view=false;level.teleport_player(Vector3(10.5,.05,-8.2));await frames(30)
	interact();await frames(310);await shot("auth_main_open_inside")
	interact()
	for i in 90:
		await frames(1)
		if level.fade_rect.color.a>.999:await shot("auth_transfer_black",0);break
	await frames(60);await shot("auth_outside_B")
	interact();await frames(60);await shot("auth_returned_room1")
	FileAccess.open(OUT+"auth_capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
