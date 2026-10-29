extends Node

const OUT:="res://docs/art/experiments/room1_complete_r19/evidence/"
var room:Node3D
var camera:Camera3D
var pod:Node3D
var integrated:=false
var records:Array=[]
var prefix:=""

func _ready() -> void:call_deferred("capture")

func look(position:Vector3,target:Vector3,fov:float=55.0) -> void:
	camera.global_position=position;camera.look_at(target,Vector3.UP);camera.fov=fov

func shot(name:String) -> void:
	room.call("_sync_render_camera");room.call("_sync_bloom_camera")
	room.call("_sync_standard_visuals")
	if integrated:
		room.call("_sync_complete_room_pose");room.call("_sync_complete_screen_sources")
	room.call("_sync_door_glow")
	for i in 12:await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image:=get_viewport().get_texture().get_image()
	assert(image.save_png(OUT+prefix+name+".png")==OK)
	records.append({"file":prefix+name+".png","p12_pose":pod.get_state_name(),"raw":room.get("complete_raw_lightmaps") if integrated else false,"camera":str(camera.global_transform),"fov":camera.fov,"resolution":[image.get_width(),image.get_height()]})
	print("R19_SHOT ",prefix,name)

func capture() -> void:
	room=get_parent() as Node3D;integrated=room.has_method("set_complete_lightmaps")
	prefix="complete/" if integrated else "before/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT+prefix))
	for i in 20:await get_tree().process_frame
	room.call("finish_exit");room.get("review_ui").close_dialogue()
	room.set_process(false);room.set_physics_process(false)
	room.set("actor_shadow_on",false);room.call("_sync_actor_shadow")
	for key in ["paper_hero","bloom_paper_hero"]:
		var actor:Sprite3D=room.get(key)
		if actor:actor.visible=false
	(room.get("info") as Label).get_parent().hide()
	var ui:Node=room.get("review_ui")
	if ui.get("pause_button"):(ui.get("pause_button") as Control).hide()
	camera=room.get_node("ReviewCamera") as Camera3D;pod=room.get("standard")
	for opened in [false,true]:
		pod.set_open_immediate(opened)
		var pose:="open" if opened else "closed"
		for row in [["front",-4.75],["back",-8.0]]:
			for column in [["left",3.525],["middle",10.5],["right",17.475]]:
				room.call("teleport_player",Vector3(column[1],.05,row[1]));camera.fov=50
				await shot("game_"+str(row[0])+"_"+str(column[0])+"_"+pose)
		look(Vector3(10.5,13,6.5),Vector3(10.5,0,-4.75),78)
		await shot("whole_room_"+pose)
		look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44)
		await shot("p12_oblique_"+pose)
	if integrated:
		for record:Dictionary in room.get("room_pod_records"):
			var current:Node3D=room.get("room_pods")[record.id]
			look(current.to_global(Vector3(-1.0,1.4,2.9)),current.to_global(Vector3(0,.35,0)),48)
			await shot("pod_"+str(record.id))
		for view in [
			["corner_rear_left",Vector3(2.5,1.9,-6.2),Vector3(.2,1.45,-9.25)],
			["corner_rear_right",Vector3(18.5,1.9,-6.2),Vector3(20.8,1.45,-9.25)],
			["door_header",Vector3(10.5,2.55,-4.3),Vector3(10.5,2.1,-9.25)]]:
			look(view[1],view[2],60);await shot(view[0])
		var front:MeshInstance3D=room.get_node("Shell").find_child("Wall_front",true,false)
		var old_visible:=front.visible;var old_shadow:=front.cast_shadow
		front.visible=true;front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		for view in [
			["corner_front_left",Vector3(2.5,1.9,-3.2),Vector3(.2,1.45,-.25)],
			["corner_front_right",Vector3(18.5,1.9,-3.2),Vector3(20.8,1.45,-.25)],
			["front_wall_lamp",Vector3(10.5,2.0,-5.7),Vector3(10.5,1.6,-.2)]]:
			look(view[1],view[2],70);await shot(view[0])
		front.visible=old_visible;front.cast_shadow=old_shadow
		look(Vector3(10.5,10,2.5),Vector3(10.5,.05,-4.75),80);await shot("floor_contacts")
		for raw in [true,false]:
			room.call("set_complete_lightmaps",raw)
			var label:="raw" if raw else "denoised"
			look(Vector3(2.5,1.9,-6.2),Vector3(.2,1.45,-9.25),60);await shot(label+"_corner")
			look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44);await shot(label+"_p12")
		pod.set_open_immediate(false)
		look(Vector3(2.15,1.22,-8.9),Vector3(3.525,.53,-8.29),48)
		await shot("glass_closed_tubes_on")
		pod.set_glass_visible(false);await shot("glass_hidden")
		pod.set_glass_visible(true);pod.set_tube_powered(false);await shot("glass_tubes_off")
		pod.set_tube_powered(true);pod.set_open_immediate(true)
		look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44)
		await shot("p12_open_restored")
	FileAccess.open(OUT+prefix+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
