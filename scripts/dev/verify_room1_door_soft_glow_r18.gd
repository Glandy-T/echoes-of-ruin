extends Node

const REPORT:="res://docs/art/experiments/room1_door_soft_glow_r18/source/runtime_validation.json"
var room:Node3D
var checks:Dictionary={}
var errors:Array[String]=[]

func _ready() -> void:call_deferred("_run")

func check(key:String,condition:bool) -> void:
	checks[key]=condition
	if not condition:errors.append(key)

func frames(count:int) -> void:
	for i in count:await get_tree().physics_frame

func _run() -> void:
	room=get_parent() as Node3D
	await frames(6);room.call("finish_exit")
	var material:ShaderMaterial=room.get("inner_light_material")
	var panel:MeshInstance3D=room.get("door_mesh")
	var body:StaticBody3D=room.get("door_body")
	var root:Node3D=room.get("integrated_root")
	var status:StandardMaterial3D=room.get("status_material")
	var normal_trim:ShaderMaterial=room.get("neutral_reveal")
	var panel_mesh:=panel.mesh
	var panel_front:=panel.get_surface_override_material(0)
	var status_mesh:Mesh=room.get("status_window").mesh
	var lights:Array=room.get("inner_lights")
	var vertices:Array=[]
	check("four_single_surface_diffusers",lights.size()==4)
	for light:MeshInstance3D in lights:
		var arrays:=light.mesh.surface_get_arrays(0)
		check(str(light.name)+"_4_vertices_2_triangles",arrays[Mesh.ARRAY_VERTEX].size()==4 and arrays[Mesh.ARRAY_INDEX].size()==6)
		for vertex:Vector3 in arrays[Mesh.ARRAY_VERTEX]:
			vertices.append([vertex.x,vertex.y,vertex.z])
			check(str(light.name)+"_behind_leaf_before_backdrop",vertex.z < -0.0425 and vertex.z > -0.09)
	check("no_added_light_nodes",root.find_children("*","Light3D",true,false).is_empty())
	check("idle_power_off",is_zero_approx(float(material.get_shader_parameter("passage_power"))))
	room.call("teleport_player",Vector3(10.5,0.05,-8.6))
	await frames(36)
	check("real_approach_scans",room.get("feedback_state")=="scanning")
	check("scan_power_off",is_zero_approx(float(material.get_shader_parameter("passage_power"))))
	await frames(330)
	check("real_auth_opens",room.get("feedback_state")=="pass" and room.get("door_fraction")>.95)
	check("passage_power_on",is_equal_approx(float(material.get_shader_parameter("passage_power")),1.0))
	check("status_window_green",status.albedo_color.g>.55)
	for trim:MeshInstance3D in root.find_children("JambLight_*","MeshInstance3D",true,false):
		check(str(trim.name)+"_neutral",trim.material_override==normal_trim)
		check(str(trim.name)+"_visibility",trim.visible==(trim.name!=&"JambLight_Bottom"))
	var offset:Vector3=panel.global_position-room.get("door_closed_position")
	check("same_1_52m_travel",absf(offset.x-1.52)<.001)
	check("collision_moves_with_panel",(body.global_position-room.get("body_closed_position")).is_equal_approx(offset))
	check("shader_guard_tracks_actual_leaf",absf(float(material.get_shader_parameter("leaf_min_x"))-(offset.x-.695))<.001)
	room.set("test_mode",true);room.set("test_input",Vector2(0,-1))
	await frames(110);room.set("test_input",Vector2.ZERO)
	check("actor_crosses_into_corridor",room.get("player").global_position.z < -10.0)
	await frames(270)
	check("real_close_resets",room.get("door_fraction")<.05 and room.get("feedback_state")=="idle")
	check("closed_power_off",is_zero_approx(float(material.get_shader_parameter("passage_power"))))
	room.set("chip_enabled",false);room.call("teleport_player",Vector3(10.5,0.05,-8.6))
	await frames(18)
	check("denial_window_only",room.get("feedback_state")=="denied" and status.albedo_color.r>.5 and room.get("door_fraction")<.05)
	check("denied_power_off",is_zero_approx(float(material.get_shader_parameter("passage_power"))))
	check("leaf_mesh_front_and_status_preserved",panel.mesh==panel_mesh and panel.get_surface_override_material(0)==panel_front and room.get("status_window").mesh==status_mesh)
	var shape:BoxShape3D=body.get_child(0).shape
	check("collision_dimensions_preserved",shape.size.is_equal_approx(Vector3(1.37,2.3,.085)))
	check("independent_door_glow_world",room.get("door_glow_source").own_world_3d)
	check("halo_camera_tracks_scene",room.get("door_glow_camera").global_transform.is_equal_approx(room.get("render_camera").global_transform))
	check("halo_source_depth_includes_moving_leaf",room.get("door_glow_proxies").any(func(item:Dictionary):return item.source==panel))
	check("halo_off_comparison",room.get("door_glow_overlay").visible)
	room.call("set_door_glow",false)
	check("halo_toggle_hides_overlay",not room.get("door_glow_overlay").visible)
	room.call("set_door_glow",true)
	var report:={"result":"PASS" if errors.is_empty() else "FAIL","errors":errors,"checks":checks,"diffuser_root_local_vertices":vertices,
		"leaf_mesh":panel_mesh.resource_path,"door_albedo":(panel_front as ShaderMaterial).get_shader_parameter("pixel_map").resource_path,
		"emitter_shader":material.shader.resource_path,"new_light_nodes":0,"rebaked":false,"pixel_texture_edited":false}
	FileAccess.open(REPORT,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("R18_RUNTIME ",JSON.stringify(report))
	get_tree().quit(0 if errors.is_empty() else 1)
