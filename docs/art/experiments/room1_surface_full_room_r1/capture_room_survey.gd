extends SceneTree
const OUT := "res://docs/art/experiments/room1_surface_full_room_r1/survey/"
var records: Array = []
var room: Node
var camera: Camera3D
func _initialize() -> void:
	call_deferred("capture")
func shot(name: String, kind: String) -> void:
	room._sync_render_camera()
	room._sync_bloom_camera()
	for frame in 15: await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	assert(image.save_png(OUT+name+".png") == OK)
	records.append({"file":name+".png","kind":kind,
		"camera_position":[camera.position.x,camera.position.y,camera.position.z],
		"camera_basis":str(camera.basis),"fov":camera.fov,"size":[image.get_width(),image.get_height()]})
func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	room = load("res://scenes/dev/room1_surface_full_room_r1.tscn").instantiate()
	room.lightmap_bake_override = "res://assets/art/room1_wall_finish_r4"
	get_root().add_child(room)
	for frame in 15: await process_frame
	room.position_material_review()
	room.set_process(false)
	room.set_physics_process(false)
	room.info.get_parent().visible = false
	room.set_full_surface_mode(3)
	camera = room.get_node("ReviewCamera") as Camera3D
	var index := 0
	for z in [-3.4,-5.75]:
		for x in [3.525,10.5,17.475]:
			room.teleport_player(Vector3(x,0,z))
			index += 1
			await shot("%02d_game"%index,"Unchanged gameplay camera; left/center/right in both pod rows")
	var front := room.get_node("Shell").find_child("Wall_front",true,false) as MeshInstance3D
	var was_visible := front.visible
	var shadow_setting := front.cast_shadow
	var corners := [
		["07_rear_left",Vector3(3.8,2.4,-5.7),Vector3(.2,1.5,-9.3)],
		["08_rear_right",Vector3(17.2,2.4,-5.7),Vector3(20.8,1.5,-9.3)],
		["09_front_left",Vector3(3.8,2.4,-3.8),Vector3(.2,1.5,-.2)],
		["10_front_right",Vector3(17.2,2.4,-3.8),Vector3(20.8,1.5,-.2)],
		["11_door",Vector3(10.5,2.0,-5.2),Vector3(10.5,1.45,-9.3)]]
	for view in corners:
		front.visible = str(view[0]).contains("front_") or was_visible
		front.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if str(view[0]).contains("front_") else shadow_setting
		camera.position = view[1]
		camera.look_at(view[2],Vector3.UP)
		camera.fov = 55.0
		await shot(view[0],"Temporary technical inspection camera; no saved camera/layout changes")
	front.visible = was_visible
	front.cast_shadow = shadow_setting
	for view in [["12_overview_front",Vector3(10.5,15,-1.0),Vector3(10.5,0,-4.75)],
		["13_overview_rear",Vector3(10.5,15,-8.5),Vector3(10.5,0,-4.75)]]:
		camera.position = view[1]
		camera.look_at(view[2],Vector3.UP)
		camera.fov = 70.0
		await shot(view[0],"Temporary technical overview; all20pods and floor coverage, not a proposed gameplay camera")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify({
		"geometry":room.baked_geometry_path,"irradiance":room.irradiance_path,
		"scope":"Six game views, four corner views, door, two overview cameras. Front cutaway wall shown only for technical front-corner inspection.",
		"captures":records},"  "))
	print("ROOM_SURVEY_COMPLETE",records.size())
	quit()
