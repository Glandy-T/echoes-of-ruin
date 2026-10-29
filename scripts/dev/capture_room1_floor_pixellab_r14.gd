extends Node
const OUT := "res://docs/art/experiments/room1_floor_pixellab_r14/evidence/"
var room: Node3D
var camera: Camera3D

func _ready() -> void:
	call_deferred("capture")

func sync() -> void:
	room.call("_sync_render_camera")
	room.call("_sync_bloom_camera")

func snap(name: String) -> void:
	for i in 12: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	assert(get_viewport().get_texture().get_image().save_png(OUT+name+".png")==OK)
	print("FLOOR_R14_SHOT ",name)

func overhead() -> void:
	# Technical-only view: actor is hidden, so suppress its orphan capsule shadow.
	for material: ShaderMaterial in room.get("baked_receivers"):
		material.set_shader_parameter("actor_shadow_enabled",0.0)
	camera.global_position=Vector3(10.5,15,-4.75)
	camera.look_at(Vector3(10.5,0,-4.751),Vector3(0,0,-1))
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.size=22.5
	sync()

func close_floor(point: Vector3) -> void:
	camera.projection=Camera3D.PROJECTION_PERSPECTIVE
	camera.global_position=point+Vector3(1.0,2.7,2.0 if point.z<-4.0 else -2.0)
	camera.look_at(point)
	camera.fov=58
	sync()

func capture() -> void:
	room=get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(OUT)
	for i in 15:await get_tree().process_frame
	room.call("position_structure_review")
	room.set_process(false);room.set_physics_process(false)
	(room.get("info") as Label).get_parent().hide()
	for key in ["paper_hero","bloom_paper_hero"]:
		var hero:=room.get(key) as Sprite3D
		if hero:hero.hide()
	var ui:=room.get("review_ui") as Node
	if ui and ui.get("pause_button"):(ui.get("pause_button") as Control).hide()
	camera=room.get_node("ReviewCamera") as Camera3D
	var bindings:=[]
	for material: ShaderMaterial in room.get("full_materials")["Floor_continuous_no_tile_seams"]:
		assert(material.get_shader_parameter("full_surface_kind")==1)
		assert(material.get_shader_parameter("full_surface_mode")==3)
		assert((material.get_shader_parameter("full_floor_leaks_map") as Texture2D).resource_path.contains("room1_floor_pixellab_r14"))
		bindings.append({"map":(material.get_shader_parameter("full_floor_leaks_map") as Texture2D).resource_path,"irradiance":(material.get_shader_parameter("strip_irradiance") as Texture2D).resource_path,"shader":material.shader.resource_path,"baked_energy":material.get_shader_parameter("baked_energy")})
	FileAccess.open(OUT+"floor_bindings.json",FileAccess.WRITE).store_string(JSON.stringify(bindings,"\t"))
	for enabled in [false,true]:
		room.call("set_floor_contact",enabled)
		var suffix:="after" if enabled else "before"
		camera.projection=Camera3D.PROJECTION_PERSPECTIVE
		camera.fov=50
		for material: ShaderMaterial in room.get("baked_receivers"):
			material.set_shader_parameter("actor_shadow_enabled",1.0)
		for station in [["left",3.525],["center",10.5],["right",17.475]]:
			room.call("teleport_player",Vector3(station[1],0,-4.75));sync()
			await snap("game_"+str(station[0])+"_"+suffix)
		overhead();await snap("overhead_"+suffix)
		room.call("set_base_color_mode",true);await snap("overhead_color_"+suffix)
		room.call("set_base_color_mode",false)
		close_floor(Vector3(5.275,0,-1.86));await snap("pod_contact_"+suffix)
	room.call("set_floor_contact",true)
	overhead();await snap("overhead_restored")
	var support_data:=JSON.parse_string(FileAccess.get_file_as_string("res://docs/art/experiments/room1_floor_pixellab_r14/source/pod_footprints.json")) as Dictionary
	var projected:=[]
	for pod: Dictionary in support_data["pods"]:
		var points:=[]
		for p: Array in pod["hull_godot_xz"]:
			var point:=camera.unproject_position(Vector3(p[0],0,p[1]))
			points.append([point.x,point.y])
		projected.append({"pod":pod["pod"],"points":points})
	FileAccess.open(OUT+"projected_supports.json",FileAccess.WRITE).store_string(JSON.stringify(projected,"\t"))
	# Expose all floor pixels for a separate material-only diagnostic.
	var meshes:Array[MeshInstance3D]=[]
	for mesh: MeshInstance3D in room.get_node("Pods").find_children("*","MeshInstance3D",true,false):
		if mesh.visible:meshes.append(mesh);mesh.hide()
	room.call("set_base_color_mode",true);await snap("floor_color_unoccluded")
	room.call("set_base_color_mode",false)
	for mesh in meshes:mesh.show()
	var front:=room.get_node("Shell").find_child("Wall_front",true,false) as MeshInstance3D
	front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for view in [["front_left",Vector3(0.35,0,-0.35)],["rear_left",Vector3(0.35,0,-9.15)],["front_right",Vector3(20.65,0,-0.35)],["rear_right",Vector3(20.65,0,-9.15)]]:
		var target:Vector3=view[1]
		camera.projection=Camera3D.PROJECTION_PERSPECTIVE
		camera.global_position=target+Vector3(2.2 if target.x<10 else -2.2,2.5,2.5 if target.z<-4 else -2.5)
		camera.look_at(target);camera.fov=65;sync();await snap("corner_"+str(view[0]))
	for view in [["P03",Vector3(5.275,0,-1.86)],["P06",Vector3(12.225,0,-1.86)],["P13",Vector3(5.275,0,-7.64)],["P18",Vector3(15.725,0,-7.64)],["P12_standard",Vector3(3.525,0,-7.64)],["door",Vector3(10.5,0,-9.05)]]:
		close_floor(view[1]);await snap("contact_"+str(view[0]))
	front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	get_tree().quit()
