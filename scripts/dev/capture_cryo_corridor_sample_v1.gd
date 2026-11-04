extends Node

const OUT := "res://docs/art/experiments/cryo_corridor_sample_v1/evidence/"
var room: Node3D
var records: Array = []

func _ready() -> void:
	call_deferred("run")

func frames(n: int) -> void:
	for i in n: await get_tree().process_frame

func shot(label: String, pos: Vector3, target: Vector3, fov: float = 50.0) -> void:
	var camera := room.get_node("ReviewCamera") as Camera3D
	camera.global_position = pos
	camera.look_at(target, Vector3.UP)
	camera.fov = fov
	room._sync_render_camera()
	room._sync_bloom_camera()
	await frames(12)
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.save_png(OUT+label+".png") == OK)
	records.append({"file":label+".png","camera":str(camera.global_transform),"resolution":[image.get_width(),image.get_height()]})
	print("CORRIDOR_SHOT ",label)

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	room=get_parent()
	await frames(100)
	room.finish_exit()
	room.review_ui.close_dialogue()
	room.teleport_player(Vector3(10.5,0.05,-10.7))
	await frames(200)
	room.info.get_parent().hide()
	room.set_process(false)
	room.set_physics_process(false)
	room.review_ui.hide_interaction_name(room.door_sensor)
	room.set("chip_enabled",true)
	room.set("door_occupied",true)
	room.set("scan_complete",true)
	room.set("pass_valid",true)
	room.set("door_fraction",1.0)
	room.get("door_mesh").global_position=room.get("door_closed_position")+Vector3(1.52,0,0)
	room.get("door_body").global_position=room.get("body_closed_position")+Vector3(1.52,0,0)
	room._update_feedback()
	room._sync_door_glow()
	for mode in [false,true]:
		room.corridor_view=false
		room.teleport_player(Vector3(10.5,.05,-10.7))
		for i in 20:
			room._update_occlusion()
			await frames(1)
		if room.has_method("set_sample_visible"): room.set_sample_visible(mode)
		elif mode: continue
		var prefix := "sample" if mode else "baseline"
		await shot(prefix+"_door_link",Vector3(10.5,2.2,-2.7),Vector3(10.5,0.85,-10.7))
		room.corridor_view=false
		for i in 20:
			room._update_occlusion()
			await frames(1)
		await shot(prefix+"_wall",Vector3(8.2,1.7,-9.65),Vector3(8.2,1.7,-11.9),110.0)
		await shot(prefix+"_oblique",Vector3(11.4,2.1,-10.0),Vector3(8.2,.95,-10.7))
		await shot(prefix+"_floor",Vector3(8.9,6,-10.4),Vector3(8.9,0,-10.7),65.0)
		room.corridor_view=true
		room.teleport_player(Vector3(8.2,.05,-10.7))
		room.update_follow_camera()
		for i in 24:
			room._update_occlusion()
			await frames(1)
		await shot(prefix+"_reverse180",Vector3(8.2,2.25,-18.7),Vector3(8.2,.90,-10.7))
	assert(room.corridor_lamp_materials.size()==2)
	assert(room.sample_lights.get_child_count()==6)
	for light in room.sample_lights.get_children():assert(light.light_cull_mask==room.SAMPLE_LAYER)
	for key in ["paper_hero","bloom_paper_hero"]:
		var actor := room.get(key) as Sprite3D
		if actor:actor.visible=false
	room.corridor_view=false
	for i in 24:
		room._update_occlusion()
		await frames(1)
	room.set_corridor_lamps(true)
	await shot("lamp_fix/on_wall",Vector3(8.2,1.7,-9.65),Vector3(8.2,1.7,-11.9),110.0)
	room.set_corridor_lamps(false)
	await shot("lamp_fix/off_wall",Vector3(8.2,1.7,-9.65),Vector3(8.2,1.7,-11.9),110.0)
	room.set_corridor_lamps(true)
	await shot("lamp_fix/restored_wall",Vector3(8.2,1.7,-9.65),Vector3(8.2,1.7,-11.9),110.0)
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
