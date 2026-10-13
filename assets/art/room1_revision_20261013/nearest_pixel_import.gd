@tool
extends EditorScenePostImport

## Apply only to this Room 1 candidate's GLBs; no global project filter changes.
func _post_import(scene: Node) -> Object:
	_apply_to_node(scene)
	return scene

func _apply_to_node(node: Node) -> void:
	if node is MeshInstance3D:
		var mesh_instance := node as MeshInstance3D
		if mesh_instance.mesh:
			for surface in mesh_instance.mesh.get_surface_count():
				var material := mesh_instance.mesh.surface_get_material(surface)
				if material is BaseMaterial3D:
					material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	for child in node.get_children():
		_apply_to_node(child)
