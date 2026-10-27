extends SceneTree
const OUT:="res://docs/art/experiments/room1_pod_volume_v4/evidence/"
var room:Node
var rows:Array=[]
func _initialize()->void:call_deferred("capture")
func shot(name:String)->void:
	for i in 15:await process_frame
	await RenderingServer.frame_post_draw
	var image:=get_root().get_texture().get_image();assert(image.save_png(OUT+name+".png")==OK)
	rows.append({"file":name+".png","new":room.revised,"open":room.opened,"view":room.view_index,"glass_visible":room.glass_visible,"chamber":room.chamber_powered,"reflections":room.reflections_on})
func capture()->void:
	room=load("res://scenes/dev/room1_pod_volume_review_v4.tscn").instantiate();get_root().add_child(room)
	if not room.has_method("set_state"):push_error("Pod review script failed to load");quit(2);return
	for i in 15:await process_frame
	room.info.visible=false
	for revised in [false,true]:
		for pose in [false,true]:
			room.set_state(revised,pose);room.set_view(0);await shot(("new" if revised else "old")+("_open" if pose else "_closed"))
	room.set_state(true,true)
	for view in [1,2,4,5]:room.set_view(view);await shot("new_open_view_"+str(view))
	room.set_state(true,false);room.set_view(3);await shot("new_glass_powered")
	room.set_glass_visible(false);await shot("new_glass_removed_control")
	room.set_glass_visible(true);room.set_chamber_power(false);await shot("new_glass_unpowered")
	room.set_chamber_power(true);room.set_reflections(false);await shot("new_glass_no_reflection_control")
	room.set_reflections(true);room.set_chamber_power(true);await shot("new_glass_restored")
	room.set_state(false,false);await shot("old_glass_powered")
	for revised in [false,true]:
		room.set_state(revised,false);room.camera.position=Vector3(1.1,1.15,2.1);room.camera.look_at(Vector3(0,.56,1.04));room.camera.fov=35
		await shot("new_display_close" if revised else "old_display_close")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(rows))
	print("POD_VOLUME_V4_CAPTURE_COMPLETE");quit()
