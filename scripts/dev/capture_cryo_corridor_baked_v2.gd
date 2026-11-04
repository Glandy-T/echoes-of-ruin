extends Node
const OUT := "res://docs/art/experiments/cryo_corridor_baked_v2/evidence/"
var room: Node3D
var records: Array = []
func _ready() -> void:call_deferred("run")
func frames(n: int) -> void:
	for i in n:await get_tree().process_frame
func shot(name: String,pos: Vector3,target: Vector3,fov: float) -> void:
	var camera := room.get_node("ReviewCamera") as Camera3D
	camera.global_position=pos;camera.look_at(target,Vector3.UP);camera.fov=fov
	room._sync_render_camera();room._sync_bloom_camera()
	await frames(14)
	await RenderingServer.frame_post_draw
	var im := get_viewport().get_texture().get_image()
	assert(im.save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","camera":str(camera.global_transform),"fov":fov,"raw":room.raw_corridor_light,"realtime_lights_visible":room.sample_lights.visible})
	print("BAKED_SHOT ",name)
func run() -> void:
	room=get_parent()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	await frames(100)
	room.finish_exit();room.review_ui.close_dialogue()
	room.teleport_player(Vector3(8.2,.05,-10.7))
	await frames(80)
	room.set_process(false);room.set_physics_process(false)
	room.info.get_parent().hide();room.review_ui.hide_interaction_name(room.door_sensor)
	for raw in [true,false]:
		room.set_corridor_raw(raw)
		var prefix := "raw" if raw else "denoised"
		room.corridor_view=true;room.update_follow_camera()
		for i in 24:room._update_occlusion();await frames(1)
		await shot(prefix+"_game",Vector3(8.2,2.25,-18.7),Vector3(8.2,.90,-10.7),50)
		room.corridor_view=false
		for i in 24:room._update_occlusion();await frames(1)
		for key in ["paper_hero","bloom_paper_hero"]:
			var actor := room.get(key) as Sprite3D
			if actor:actor.visible=false
		await shot(prefix+"_north_wall",Vector3(8.2,1.7,-9.65),Vector3(8.2,1.7,-11.9),110)
		await shot(prefix+"_south_wall",Vector3(8.2,1.7,-11.75),Vector3(8.2,1.7,-9.5),110)
		await shot(prefix+"_floor",Vector3(8.9,6,-10.4),Vector3(8.9,0,-10.7),65)
		await shot(prefix+"_west_wall_feet",Vector3(7.2,1.15,-10.7),Vector3(6.7,.2,-11.75),75)
		await shot(prefix+"_east_wall_feet",Vector3(9.2,1.15,-10.7),Vector3(9.7,.2,-9.65),75)
		await shot(prefix+"_north_east_foot",Vector3(9.2,1.15,-10.7),Vector3(9.7,.2,-11.75),75)
		await shot(prefix+"_south_west_foot",Vector3(7.2,1.15,-10.7),Vector3(6.7,.2,-9.65),75)
		await shot(prefix+"_lamp_close",Vector3(8.2,2.9,-10.0),Vector3(8.2,3.05,-11.897),65)
		for key in ["paper_hero","bloom_paper_hero"]:
			var actor := room.get(key) as Sprite3D
			if actor:actor.visible=true
	room.set_corridor_raw(false)
	for key in ["paper_hero","bloom_paper_hero"]:
		var actor := room.get(key) as Sprite3D
		if actor:actor.visible=false
	await shot("on_wall",Vector3(8.2,1.7,-9.65),Vector3(8.2,1.7,-11.9),110)
	room.set_corridor_lamps(false)
	await shot("off_wall",Vector3(8.2,1.7,-9.65),Vector3(8.2,1.7,-11.9),110)
	room.set_corridor_lamps(true)
	await shot("restored_wall",Vector3(8.2,1.7,-9.65),Vector3(8.2,1.7,-11.9),110)
	assert(not room.sample_lights.visible)
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
