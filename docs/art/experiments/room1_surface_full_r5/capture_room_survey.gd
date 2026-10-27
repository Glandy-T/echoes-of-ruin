extends SceneTree
const OUT := "res://docs/art/experiments/room1_surface_full_r5/survey/"
var room: Node
var camera: Camera3D
var records: Array=[]
func _world_bounds(mesh: MeshInstance3D) -> AABB:
	var local := mesh.get_aabb()
	var result := AABB()
	var first := true
	for corner in 8:
		var point := mesh.global_transform * local.get_endpoint(corner)
		if first: result = AABB(point, Vector3.ZERO); first = false
		else: result = result.expand(point)
	return result
func _initialize() -> void: call_deferred("capture")
func _snap(name:String, note:String)->void:
	for _i in 15: await process_frame
	await RenderingServer.frame_post_draw
	var image:=get_root().get_texture().get_image(); assert(image.get_width()==1280 and image.get_height()==720); assert(image.save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","mode":room.full_mode,"base_color":room.base_color_mode,"note":note,"camera":[camera.global_position.x,camera.global_position.y,camera.global_position.z],"fov":camera.fov,"geometry":room.baked_geometry_path,"irradiance":room.irradiance_path,"hdr":"r4 continuous strip UV2 irradiance; unchanged"})
func _look(pos:Vector3,target:Vector3,fov:float=50.0)->void: camera.global_position=pos; camera.look_at(target); camera.fov=fov; room._sync_render_camera(); room._sync_bloom_camera()
func capture()->void:
	DirAccess.make_dir_recursive_absolute(OUT); room=load("res://scenes/dev/room1_surface_full_r5.tscn").instantiate(); get_root().add_child(room)
	for _i in 15: await process_frame
	room.position_structure_review(); room.set_process(false); room.set_physics_process(false); room.info.get_parent().visible=false; room.set_full_surface_mode(3); room.set_base_color_mode(false); camera=room.get_node("ReviewCamera") as Camera3D
	for station in [{"n":"game_left_front","p":Vector3(3.525,0,-3.4)},{"n":"game_center_front","p":Vector3(10.5,0,-3.4)},{"n":"game_right_front","p":Vector3(17.475,0,-3.4)},{"n":"game_left_back","p":Vector3(3.525,0,-5.75)},{"n":"game_center_back","p":Vector3(10.5,0,-5.75)},{"n":"game_right_back","p":Vector3(17.475,0,-5.75)}]: room.teleport_player(station.p);camera.fov=50;room._sync_render_camera();room._sync_bloom_camera();await _snap(station.n,"game coverage")
	# The inherited game camera keeps Wall_front shadow-only for the cutaway.
	# Temporarily render it only for the following technical coverage, then restore.
	var front := room.get_node("Shell").find_child("Wall_front", true, false) as MeshInstance3D
	assert(front != null)
	front.visible = true
	front.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	# These face each physical corner rather than merely looking across the room:
	# they expose the connected side/rear/front textures and diffuser returns.
	for corner in [{"n":"corner_front_left","p":Vector3(2.8,2.1,-2.8),"t":Vector3(0.25,1.35,-0.25)},{"n":"corner_front_right","p":Vector3(18.2,2.1,-2.8),"t":Vector3(20.75,1.35,-0.25)},{"n":"corner_rear_left","p":Vector3(2.8,2.1,-6.7),"t":Vector3(0.25,1.35,-9.25)},{"n":"corner_rear_right","p":Vector3(18.2,2.1,-6.7),"t":Vector3(20.75,1.35,-9.25)}]: _look(corner.p,corner.t,56);await _snap(corner.n,"corner seam, adjacent wall maps and floor continuity")
	var front_bounds := _world_bounds(front)
	print("R5_WALL_FRONT_AABB ", front_bounds)
	# Wall_front occupies z=-0.2.  The following is an explicit technical-only
	# inside view; gameplay immediately returns it to the inherited shadow-only cutaway.
	var front_center := front_bounds.get_center()
	_look(front_center + Vector3(0.0, 0.15, -6.0), front_center, 55);await _snap("front_wall_actual","diagnostic-only rendered Wall_front from room interior; full lamp-to-wall-foot coverage, z=-0.2")
	front.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	var header := room.get_node("Shell").find_child("Wall_rear_door_header", true, false) as MeshInstance3D
	assert(header != null)
	var header_target := _world_bounds(header).get_center()
	_look(header_target + Vector3(0.0, 1.45, 4.9), header_target + Vector3(0.0, 0.1, 0.0), 55);await _snap("door_header_lit","door header with adjacent rear sections, shared world-X rear mapping and continuous lamp")
	_look(Vector3(10.5,14.0,-1.0),Vector3(10.5,0,-4.75),53);await _snap("overview_front","full room overview from front")
	_look(Vector3(10.5,14.0,-8.5),Vector3(10.5,0,-4.75),53);await _snap("overview_rear","full room overview from rear")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify({"scene":"room1_surface_full_r5.tscn","mode":3,"front_wall_aabb":{"position":[front_bounds.position.x,front_bounds.position.y,front_bounds.position.z],"size":[front_bounds.size.x,front_bounds.size.y,front_bounds.size.z]},"captures":records,"coverage":"six game, four physical corner seams, actual front wall, door header, two whole-room overviews"}));print("ROOM1_SURFACE_FULL_R5_SURVEY_COMPLETE");quit()
