extends SceneTree
const OUT := "res://docs/art/experiments/room1_seam_contact_r6/evidence/"
var room: Node
var camera: Camera3D
var records: Array = []
func _initialize() -> void: call_deferred("capture")
func _snap(name: String) -> void:
	for i in 15: await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	assert(image.save_png(OUT + name + ".png") == OK)
	records.append({"file": name + ".png", "fixed": room.seam_contact_fixed, "base_color": room.base_color_mode, "fov": camera.fov, "position": camera.global_position})
func capture() -> void:
	room=load("res://scenes/dev/room1_seam_contact_r6.tscn").instantiate(); get_root().add_child(room)
	for i in 20: await process_frame
	room.position_structure_review(); room.set_process(false); room.set_physics_process(false); room.info.get_parent().visible=false
	camera=room.get_node("ReviewCamera") as Camera3D
	room.set_full_surface_mode(3)
	for fixed in [false,true]:
		room.set_seam_contact_fixed(fixed)
		for station in [{"tag":"left","x":3.525},{"tag":"center","x":10.5},{"tag":"right","x":17.475}]:
			room.teleport_player(Vector3(station.x,0,-4.75));camera.fov=50;room._sync_render_camera();room._sync_bloom_camera()
			await _snap("game_%s_%s" % [station.tag,"r6" if fixed else "r5"])
	# Exact restoration after color-only diagnosis in the corrected scene.
	room.set_base_color_mode(true);await _snap("game_right_base_color")
	room.set_base_color_mode(false);await _snap("game_right_after_n")
	# Explicitly render cutaway front for technical inspection only.
	var front := room.get_node("Shell").find_child("Wall_front",true,false) as MeshInstance3D
	front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for view in [{"name":"front_wall","pos":Vector3(10.5,1.85,-6.2),"target":Vector3(10.5,1.7,-.2)},{"name":"corner_front_left","pos":Vector3(2.8,2.1,-2.8),"target":Vector3(.25,1.35,-.25)},{"name":"corner_rear_right","pos":Vector3(18.2,2.1,-6.7),"target":Vector3(20.75,1.35,-9.25)}]:
		camera.global_position=view.pos;camera.look_at(view.target);camera.fov=55;room._sync_render_camera();room._sync_bloom_camera();await _snap(view.name)
	front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records))
	print("ROOM1_SEAM_CONTACT_R6_COMPLETE");quit()
