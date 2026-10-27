extends SceneTree

func _init() -> void:
	var records: Array = []
	for name in ["room1_shell_full_r1", "room1_layout_review_r1", "pod_closed_v3", "pod_open_v3"]:
		var path: String = "res://assets/art/room1_revision_20261013/" + str(name) + ".glb"
		var packed := load(path) as PackedScene
		if packed == null:
			push_error("Could not load imported model: " + name)
			quit(1)
			return
		var node := packed.instantiate()
		var record := {"file": name + ".glb", "mesh_instances": 0, "surfaces": 0,
			"textured_surfaces": 0, "filters": []}
		_read_node(node, record)
		records.append(record)
		node.free()
	var output := FileAccess.open("res://import_readback.json", FileAccess.WRITE)
	output.store_string(JSON.stringify({"engine": Engine.get_version_info()["string"],
		"status": "actual imported PackedScene resources loaded and instantiated",
		"scope": "File import only. No gameplay, collision, animation or rendered art approval.",
		"models": records}, "  "))
	output.close()
	print("ROOM1_IMPORTED_RESOURCE_READBACK_COMPLETE")
	quit()

func _read_node(node: Node, record: Dictionary) -> void:
	if node is MeshInstance3D:
		var instance := node as MeshInstance3D
		record["mesh_instances"] += 1
		for surface in instance.mesh.get_surface_count():
			record["surfaces"] += 1
			var material := instance.mesh.surface_get_material(surface)
			if material is BaseMaterial3D:
				if material.albedo_texture:
					record["textured_surfaces"] += 1
					if not record["filters"].has(material.texture_filter):
						record["filters"].append(material.texture_filter)
	for child in node.get_children():
		_read_node(child, record)
