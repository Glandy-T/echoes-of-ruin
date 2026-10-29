extends SceneTree

const OUT:="res://docs/art/experiments/room1_complete_r19/evidence/"

func _initialize() -> void:call_deferred("run")

func frames(count:int) -> void:
	for i in count:await physics_frame

func shot(name:String) -> void:
	for i in 10:await process_frame
	await RenderingServer.frame_post_draw
	assert(root.get_texture().get_image().save_png(OUT+name+".png")==OK)
	print("R19_PLAYABLE_SHOT ",name)

func tap(action:StringName) -> void:
	var event:=InputEventAction.new();event.action=action;event.pressed=true
	Input.parse_input_event(event);await process_frame;await process_frame
	event=InputEventAction.new();event.action=action;event.pressed=false
	Input.parse_input_event(event);await process_frame

func run() -> void:
	assert(change_scene_to_file("res://scenes/core/title_screen.tscn")==OK)
	await frames(12);await shot("formal_title")
	current_scene.start_button.pressed.emit()
	await frames(30)
	var room:Node3D=current_scene
	assert(room.scene_file_path=="res://scenes/areas/military_facility/cryo_room_4f_01_3d.tscn")
	assert(room.get("review_ui").is_dialogue_open())
	await shot("formal_opening_dialogue")
	await tap(&"dialogue_advance");await tap(&"dialogue_advance")
	await frames(430) # Allow the inherited exit sequence to finish naturally.
	assert(not room.get("input_locked"))
	await shot("formal_gameplay_start")
	room.set("test_mode",true);room.set("test_input",Vector2(0,1));await frames(95)
	room.set("test_input",Vector2.ZERO);await frames(12)
	await shot("formal_main_aisle")
	# Door presentation uses its real sensor/authorization, not forced fractions.
	room.call("teleport_player",Vector3(10.5,.05,-8.6))
	await frames(180);await shot("formal_door_opening")
	await frames(180);await shot("formal_door_open")
	assert(room.get("feedback_state")=="pass" and room.get("door_fraction")>.95)
	current_scene.queue_free();await process_frame
	quit()
