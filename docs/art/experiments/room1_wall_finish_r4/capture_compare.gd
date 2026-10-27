extends SceneTree
const OUT := "res://docs/art/experiments/room1_wall_finish_r4/evidence/"
var room: Node
var camera: Camera3D
var records: Array = []
func _initialize() -> void:
	call_deferred("capture")
func shot(name: String, kind: String) -> void:
	room._sync_render_camera()
	room._sync_bloom_camera()
	for frame in 15: await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	assert(image.save_png(OUT+name+".png") == OK)
	records.append({"file":name+".png","kind":kind,"size":[image.get_width(),image.get_height()],
		"camera_position":[camera.position.x,camera.position.y,camera.position.z],
		"basis":str(camera.basis),"fov":camera.fov,"geometry":room.baked_geometry_path,
		"irradiance":room.irradiance_path})
func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	for version in ["r3","r4"]:
		room = load("res://scenes/dev/room1_surface_sample_r1.tscn").instantiate()
		room.lightmap_bake_override = "res://assets/art/room1_corner_quality_r3" if version=="r3" else "res://assets/art/room1_wall_finish_r4"
		get_root().add_child(room)
		for frame in 15: await process_frame
		room.position_surface_review()
		room.set_process(false)
		room.set_physics_process(false)
		room.info.get_parent().visible = false
		camera = room.get_node("ReviewCamera") as Camera3D
		room.set_surface_sample_mode(3)
		await shot("01_"+version+"_left_game","Original gameplay camera, sample materials")
		room.teleport_player(Vector3(10.5,0,-2.0))
		room.set_surface_sample_mode(0)
		await shot("02_"+version+"_center_game","Original center gameplay camera, header diffuser joins")
		var front := room.get_node("Shell").find_child("Wall_front",true,false) as MeshInstance3D
		front.visible = true
		front.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		camera.position = Vector3(3.8,2.4,-3.8)
		camera.look_at(Vector3(.2,1.5,-.2),Vector3.UP)
		camera.fov = 55.0
		await shot("03_"+version+"_front_corner","Temporary inspection camera; front cutaway wall rendered")
		camera.position = Vector3(10.5,3.0,-8.3)
		camera.look_at(Vector3(10.5,1.7,-.2),Vector3.UP)
		camera.fov = 100.0
		await shot("04_"+version+"_front_wide","Temporary full-front inspection, not proposed gameplay camera")
		camera.position = Vector3(10.5,3.04,-7.3)
		camera.look_at(Vector3(10.5,3.04,-9.3),Vector3.UP)
		camera.fov = 70.0
		await shot("05_"+version+"_diffuser_close","Temporary close inspection of rear/header emitting face")
		room.queue_free()
		for frame in 5: await process_frame
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"  "))
	print("WALL_FINISH_COMPARE_COMPLETE")
	quit()
