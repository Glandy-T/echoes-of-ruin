extends SceneTree

func _initialize() -> void:call_deferred("run")

func vector(v:Vector3) -> Array:return [v.x,v.y,v.z]

func run() -> void:
	var room:=load("res://scenes/dev/room1_door_soft_glow_r18.tscn").instantiate() as Node3D
	root.add_child(room)
	for i in 5:await process_frame
	room.call("finish_exit")
	var pods:Array=[]
	var variants:=[2,0,3,1,0,2,1,3,0,2,1,0,2,3,1,2,0,1,3,0]
	var finish:RefCounted=room.get("pod_finish")
	var numbered_root:="res://assets/art/room1_complete_r19/numbered/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(numbered_root))
	for number in range(1,21):
		var id:="P%02d"%number
		var pod:Node3D=room.get_node("Pods/"+id)
		var t:=pod.global_transform
		finish.call("set_pod_number",number);finish.call("apply",variants[number-1],true)
		var maps:Dictionary={}
		for material_entry:Dictionary in finish.get("entries"):
			var role:String=material_entry.role
			if maps.has(role):continue
			var texture:Texture2D=(material_entry.material as ShaderMaterial).get_shader_parameter("color_map")
			if role in ["lid","shell_end"]:
				var image:=texture.get_image()
				if image.is_compressed():assert(image.decompress()==OK)
				var path:=numbered_root+id+"_"+role+".png"
				assert(image.save_png(path)==OK);maps[role]=path.trim_prefix("res://")
			else:maps[role]=texture.resource_path.trim_prefix("res://")
		pods.append({"id":id,"number":number,"basis_columns":[vector(t.basis.x),vector(t.basis.y),vector(t.basis.z)],"origin":vector(t.origin),"determinant":t.basis.determinant(),"variant_index":variants[number-1],"bake_color_maps":maps})
	finish.call("set_pod_number",12);finish.call("apply",0,true)
	var current:Node3D=room.get("standard")
	var old_bodies:Array=[]
	for body:CollisionObject3D in room.find_children("*","CollisionObject3D",true,false):
		if str(body.name).begins_with("Solid_P") or str(body.name).begins_with("OpenP12_"):
			old_bodies.append({"path":str(room.get_path_to(body)),"layer":body.collision_layer})
	var data:={"source_scene":room.scene_file_path,"pods":pods,"p12_screen":{"name":current.get("screen_name"),"status":current.get("screen_status"),"powered":current.get("screen_powered")},"old_bodies":old_bodies,"window_lit_pods":room.get("window_lit_pods"),"baked_energy":room.get("continuous_baked_energy")}
	FileAccess.open("res://docs/art/experiments/room1_complete_r19/source/layout_before.json",FileAccess.WRITE).store_string(JSON.stringify(data,"\t"))
	print("R19_LAYOUT ",JSON.stringify(data))
	room.queue_free();await process_frame;quit()
