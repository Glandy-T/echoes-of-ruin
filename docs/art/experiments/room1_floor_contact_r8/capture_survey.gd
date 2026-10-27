extends SceneTree

const OUT := "res://docs/art/experiments/room1_floor_contact_r8/survey/"
var room: Node
var camera: Camera3D
var records: Array = []

func _initialize() -> void:
	call_deferred("capture")

func _snap(name: String, note: String) -> void:
	for _i in 15: await process_frame
	await RenderingServer.frame_post_draw
	var image := get_root().get_texture().get_image()
	assert(image.get_width() == 1280 and image.get_height() == 720)
	assert(image.save_png(OUT + name + ".png") == OK)
	records.append({"file":name+".png","note":note,"position":[camera.global_position.x,camera.global_position.y,camera.global_position.z],"fov":camera.fov,"irradiance":room.irradiance_path})

func _look(pos: Vector3, target: Vector3, fov: float = 50.0) -> void:
	camera.global_position=pos; camera.look_at(target); camera.fov=fov
	room._sync_render_camera(); room._sync_bloom_camera()

func _game(x: float, z: float) -> void:
	room.teleport_player(Vector3(x,0,z)); camera.fov=50.0
	room._sync_render_camera(); room._sync_bloom_camera()

func capture() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	room=load("res://scenes/dev/room1_floor_contact_r8.tscn").instantiate(); get_root().add_child(room)
	for _i in 20: await process_frame
	room.position_structure_review(); room.set_process(false); room.set_physics_process(false); room.info.get_parent().visible=false
	room.set_full_surface_mode(3); room.set_floor_contact(true); room.set_surface_lighting(true)
	camera=room.get_node("ReviewCamera") as Camera3D
	for station in [{"tag":"game_left_front","x":3.525,"z":-3.4},{"tag":"game_center_front","x":10.5,"z":-3.4},{"tag":"game_right_front","x":17.475,"z":-3.4},{"tag":"game_left_back","x":3.525,"z":-5.75},{"tag":"game_center_back","x":10.5,"z":-5.75},{"tag":"game_right_back","x":17.475,"z":-5.75}]:
		_game(station.x,station.z); await _snap(station.tag,"C default gameplay coverage")
	# The live camera uses a front cutaway. Restore the physical wall only for the four actual corners and front wall check.
	var front:=room.get_node("Shell").find_child("Wall_front",true,false) as MeshInstance3D
	front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for corner in [{"tag":"corner_front_left","pos":Vector3(2.8,2.1,-2.8),"target":Vector3(.25,1.35,-.25)},{"tag":"corner_front_right","pos":Vector3(18.2,2.1,-2.8),"target":Vector3(20.75,1.35,-.25)},{"tag":"corner_rear_left","pos":Vector3(2.8,2.1,-6.7),"target":Vector3(.25,1.35,-9.25)},{"tag":"corner_rear_right","pos":Vector3(18.2,2.1,-6.7),"target":Vector3(20.75,1.35,-9.25)}]:
		_look(corner.pos,corner.target,56); await _snap(corner.tag,"physical wall-floor corner; contact border coverage")
	_look(Vector3(10.5,1.85,-6.2),Vector3(10.5,1.7,-.2),55); await _snap("front_wall_actual","actual front wall and front floor boundary")
	front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	# Threshold shows the deliberate rear-door break in the rear wall-floor border.
	_look(Vector3(10.5,1.65,-6.2),Vector3(10.5,0.1,-9.32),55); await _snap("door_threshold","rear door threshold and perimeter deposit interruption")
	_look(Vector3(10.5,24,-1),Vector3(10.5,0,-4.75),53); await _snap("overview_front","all 20 pod contacts plus front perimeter")
	_look(Vector3(10.5,24,-8.5),Vector3(10.5,0,-4.75),53); await _snap("overview_rear","all 20 pod contacts plus rear threshold")
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify({"scene":"room1_floor_contact_r8.tscn","captures":records,"coverage":"6 gameplay + 4 physical corners + front wall + threshold + 2 overviews = 14"}))
	print("ROOM1_FLOOR_CONTACT_R8_SURVEY_COMPLETE")
	quit()
