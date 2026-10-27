extends SceneTree
const OUT := "res://docs/art/experiments/room1_wall_finish_r4/diagnosis/"
func _initialize() -> void:
	call_deferred("inspect")
func inspect() -> void:
	DirAccess.make_dir_recursive_absolute(OUT)
	var room: Node = load("res://scenes/dev/room1_surface_sample_r1.tscn").instantiate()
	room.lightmap_bake_override = "res://assets/art/room1_corner_quality_r3"
	get_root().add_child(room)
	for frame in 10: await process_frame
	var records: Array = []
	for name in ["Wall_front","Wall_left","Wall_right","Wall_rear_left","Wall_rear_right","Wall_rear_door_header"]:
		var mesh := room.get_node("Shell").find_child(name,true,false) as MeshInstance3D
		for surface in mesh.mesh.get_surface_count():
			var mat := mesh.get_active_material(surface) as ShaderMaterial
			var arrays := mesh.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var uv: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
			var rows: Array = []
			for i in vertices.size():
				var p := mesh.global_transform * vertices[i]
				rows.append([p.x,p.y,p.z,uv[i].x,uv[i].y])
			var entry := {"wall":name,"surface":surface,"shader":mat.shader.resource_path,
				"has_emission":mat.get_shader_parameter("has_emission_map"),"vertices_world_uv0":rows}
			for parameter in ["color_map","emission_map"]:
				var texture := mat.get_shader_parameter(parameter) as Texture2D
				if texture:
					var filename := "%s_%s_%s.png" % [name,surface,parameter]
					texture.get_image().save_png(OUT+filename)
					entry[parameter]={"path":texture.resource_path,"size":[texture.get_width(),texture.get_height()],"file":filename}
			records.append(entry)
	FileAccess.open(OUT+"wall_channels.json",FileAccess.WRITE).store_string(JSON.stringify(records,"  "))
	print("WALL_CHANNELS_INSPECTED")
	quit()
