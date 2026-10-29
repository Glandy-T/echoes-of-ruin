extends Node
const OUT := "res://docs/art/experiments/room1_pod_pixellab_r16/evidence/"
const DIAGNOSTIC := preload("res://scripts/dev/pod_color_diagnostic_r16.gdshader")
var room:Node3D
var camera:Camera3D
var pod:Node3D
var records:Array=[]
var diagnostic_snapshots:Array[Dictionary]=[]

func _ready() -> void:
	call_deferred("capture")

func look(position: Vector3,target: Vector3,fov: float) -> void:
	camera.global_position=position;camera.look_at(target);camera.fov=fov
	room.call("_sync_render_camera");room.call("_sync_bloom_camera")

func oblique() -> void:
	look(Vector3(1.775,1.8,-4.45),Vector3(3.65,.43,-7.65),44)

func head_view() -> void:
	look(Vector3(2.15,1.22,-8.9),Vector3(3.525,.53,-8.29),48)

func shot(name: String) -> void:
	for i in 12:
		room.call("_sync_standard_visuals")
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image:=get_viewport().get_texture().get_image()
	assert(image.save_png(OUT+name+".png")==OK)
	records.append({"file":name+".png","pose":pod.get_state_name(),"pixel_variant":room.get("pod_variant"),"new_finish":room.get("pod_finish_on"),"size":[image.get_width(),image.get_height()],"camera":[camera.global_position.x,camera.global_position.y,camera.global_position.z],"fov":camera.fov})
	print("POD_R16_SHOT ",name)

func diagnostic(active: bool) -> void:
	if active:
		diagnostic_snapshots.clear()
		for entry: Dictionary in room.get("pod_finish").get("entries"):
			var material:ShaderMaterial=entry.material
			var params:Dictionary={}
			for uniform: Dictionary in material.shader.get_shader_uniform_list():
				params[uniform.name]=material.get_shader_parameter(uniform.name)
			diagnostic_snapshots.append({"material":material,"shader":material.shader,"params":params})
			material.shader=DIAGNOSTIC
			material.set_shader_parameter("color_map",params["color_map"])
			material.set_shader_parameter("base_color",params["base_color"])
	else:
		for snapshot in diagnostic_snapshots:
			var material:ShaderMaterial=snapshot.material
			material.shader=snapshot.shader
			for key in snapshot.params:material.set_shader_parameter(key,snapshot.params[key])
		diagnostic_snapshots.clear()

func mesh_signature() -> Dictionary:
	var result:Dictionary={}
	for mesh:MeshInstance3D in pod.get_model_root().find_children("*","MeshInstance3D",true,false):
		var surfaces:Array=[]
		for surface in mesh.mesh.get_surface_count():
			var arrays:=mesh.mesh.surface_get_arrays(surface)
			surfaces.append({"vertices":(arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).to_byte_array().hex_encode().sha256_text(),"uv0":(arrays[Mesh.ARRAY_TEX_UV] as PackedVector2Array).to_byte_array().hex_encode().sha256_text(),"uv2":(arrays[Mesh.ARRAY_TEX_UV2] as PackedVector2Array).to_byte_array().hex_encode().sha256_text(),"indices":(arrays[Mesh.ARRAY_INDEX] as PackedInt32Array).to_byte_array().hex_encode().sha256_text()})
		result[str(mesh.name)]=surfaces
	return result

func protected_signature() -> Dictionary:
	var result:Dictionary={}
	for mesh:MeshInstance3D in pod.get_model_root().find_children("*","MeshInstance3D",true,false):
		if not str(mesh.name) in ["PodGlass","PodDisplay","PodTubeDiffuser_L","PodTubeDiffuser_R","PodTubeHousing_L","PodTubeHousing_R"]:continue
		var material:=mesh.get_active_material(0) as ShaderMaterial
		var params:Dictionary={}
		for uniform: Dictionary in material.shader.get_shader_uniform_list():
			var value:Variant=material.get_shader_parameter(uniform.name)
			if value is Texture2D:params[uniform.name]=(value as Texture2D).get_image().get_data().hex_encode().sha256_text()
		result[str(mesh.name)]={"shader":material.shader.resource_path,"textures":params}
	return result

func capture() -> void:
	room=get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(OUT)
	for i in 20:await get_tree().process_frame
	room.call("position_structure_review")
	room.set_process(false);room.set_physics_process(false)
	(room.get("info") as Label).get_parent().hide()
	for key in ["paper_hero","bloom_paper_hero"]:
		var hero:=room.get(key) as Sprite3D
		if hero:hero.hide()
	var ui:=room.get("review_ui") as Node
	if ui and ui.get("pause_button"):(ui.get("pause_button") as Control).hide()
	camera=room.get_node("ReviewCamera") as Camera3D;pod=room.get("standard") as Node3D
	pod.set_actor_shadow_parameters(Vector3.ZERO,Vector3.ZERO,Vector3.UP,false)
	var original_meshes:=mesh_signature();var protected_before:=protected_signature()
	var variants:=[-1,0] if OS.get_cmdline_user_args().has("--initial") else [-1,0,1,2,3]
	var all_bindings:Dictionary={}
	for variant:int in variants:
		room.call("set_pod_finish",maxi(0,variant),variant>=0)
		var label:String="before" if variant<0 else ["a","b","c","d"][variant]
		all_bindings[label]=room.get("pod_finish").call("bindings")
		for opened:bool in [false,true]:
			pod.set_open_immediate(opened)
			var pose:="open" if opened else "closed"
			oblique();await shot("oblique_"+label+"_"+pose)
			diagnostic(true);await shot("color_"+label+"_"+pose);diagnostic(false)
			look(Vector3(1.8,1.6,-7.1),Vector3(3.525,.35,-7.65),55);await shot("side_"+label+"_"+pose)
			head_view();await shot("head_"+label+"_"+pose)
			if variant in [-1,0]:
				room.call("teleport_player",Vector3(3.525,0,-4.75));camera.fov=50
				room.call("_sync_render_camera");room.call("_sync_bloom_camera");await shot("game_"+label+"_"+pose)
	room.call("set_pod_finish",0,true)
	pod.set_open_immediate(true);oblique();await shot("a_open_restored")
	look(Vector3(4.1,1.1,-5.4),Vector3(3.525,.56,-6.58),38);await shot("screen_unchanged")
	pod.set_open_immediate(false);head_view();await shot("glass_on")
	pod.set_glass_visible(false);await shot("glass_hidden")
	pod.set_glass_visible(true);pod.set_tube_powered(false);await shot("glass_tubes_off")
	pod.set_tube_powered(true);await shot("glass_restored")
	pod.request_open();await get_tree().create_timer(2.6).timeout
	assert(pod.get_state_name()=="open");oblique();await shot("animation_open")
	pod.request_close();await get_tree().create_timer(2.6).timeout
	assert(pod.get_state_name()=="closed");oblique();await shot("animation_closed")
	assert(mesh_signature()==original_meshes,"Material-only revision changed geometry or UVs.")
	assert(protected_signature()==protected_before,"Glass, screen or tube textures/shaders changed.")
	FileAccess.open(OUT+"material_bindings.json",FileAccess.WRITE).store_string(JSON.stringify(all_bindings,"\t"))
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	FileAccess.open(OUT+"runtime_scope.json",FileAccess.WRITE).store_string(JSON.stringify({"opaque_surface_count":room.get("pod_finish").get("entries").size(),"geometry_uv_signature":original_meshes,"geometry_uv_unchanged":true,"glass_display_all_tube_parts_unchanged":true,"protected_materials":protected_before,"real_open_close_animation_passed":true,"pod_source":pod.scene_file_path,"other_19_pods":"not replaced","floor_map":"room1_floor_variants_r15","baked_energy":room.get("continuous_baked_energy")},"\t"))
	get_tree().quit()
