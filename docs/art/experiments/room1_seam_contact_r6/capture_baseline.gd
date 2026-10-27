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
	records.append({"file": name + ".png", "fixed": false, "base_color": room.base_color_mode, "fov": camera.fov, "position": camera.global_position})
func capture() -> void:
	room=load("res://scenes/dev/room1_surface_full_r5.tscn").instantiate(); get_root().add_child(room)
	for i in 20: await process_frame
	room.position_structure_review(); room.set_process(false); room.set_physics_process(false); room.info.get_parent().visible=false
	camera=room.get_node("ReviewCamera") as Camera3D
	room.set_full_surface_mode(3)
	for station in [{"tag":"left","x":3.525},{"tag":"center","x":10.5},{"tag":"right","x":17.475}]:
		room.teleport_player(Vector3(station.x,0,-4.75));camera.fov=50;room._sync_render_camera();room._sync_bloom_camera()
		await _snap("independent_r5_"+station.tag)
	quit()
