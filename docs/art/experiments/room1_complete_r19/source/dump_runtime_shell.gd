extends SceneTree

func _initialize() -> void:call_deferred("run")

func run() -> void:
	var room:=load("res://scenes/dev/room1_door_soft_glow_r18.tscn").instantiate() as Node3D
	root.add_child(room)
	for i in 4:await process_frame
	var records:Array=[]
	for name in ["Floor_continuous_no_tile_seams","Roof_hidden_for_cutaway","Wall_front","Wall_left","Wall_rear_door_header","Wall_rear_left","Wall_rear_right","Wall_right"]:
		var mesh:MeshInstance3D=room.get_node("Shell").find_child(name,true,false)
		assert(mesh,name)
		var triangles:Array=[]
		for surface in mesh.mesh.get_surface_count():
			var arrays:=mesh.mesh.surface_get_arrays(surface)
			var points:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
			var uv0:PackedVector2Array=arrays[Mesh.ARRAY_TEX_UV]
			var uv2:PackedVector2Array=arrays[Mesh.ARRAY_TEX_UV2]
			var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
			for i in range(0,indices.size(),3):
				var row:Array=[]
				for corner in 3:
					var j:=indices[i+corner]
					var p:Vector3=mesh.global_transform*points[j]
					var n:Vector3=(mesh.global_basis*normals[j]).normalized()
					row.append({"position":[p.x,p.y,p.z],"normal":[n.x,n.y,n.z],"uv0":[uv0[j].x,uv0[j].y],"uv2":[uv2[j].x,uv2[j].y]})
				triangles.append(row)
		records.append({"name":name,"mesh_resource":mesh.mesh.resource_path,"triangles":triangles})
	FileAccess.open("res://docs/art/experiments/room1_complete_r19/source/runtime_shell_triangles.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	print("R19_ACTUAL_RUNTIME_SHELL_EXPORTED")
	room.queue_free();await process_frame;quit()
