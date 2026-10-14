extends RefCounted

# Runtime-only partition of the large floor for Compatibility's per-object lights.
# World-space clipping interpolates the original UVs; source assets stay unchanged.
static func partition(shell: Node3D) -> int:
	var result := 0
	for original: MeshInstance3D in shell.find_children("*", "MeshInstance3D", true, false):
		var box := original.global_transform * original.get_aabb()
		if not original.name.contains("Floor") or box.size.x < 15.0 or box.size.z < 5.0 or box.size.y > 0.4:
			continue
		var group := Node3D.new()
		group.name = "FloorLightChunks"
		shell.add_child(group)
		for column in 5:
			for row in 2:
				var minimum := Vector2(box.position.x + box.size.x * column / 5.0, box.position.z + box.size.z * row / 2.0)
				var maximum := minimum + Vector2(box.size.x / 5.0, box.size.z / 2.0)
				var mesh := ArrayMesh.new()
				for surface in original.mesh.get_surface_count():
					var arrays := original.mesh.surface_get_arrays(surface)
					var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
					var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
					var uvs: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
					var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
					if indices.is_empty():
						for index in vertices.size():
							indices.append(index)
					var output_vertices := PackedVector3Array()
					var output_normals := PackedVector3Array()
					var output_uvs := PackedVector2Array()
					for triangle in range(0, indices.size(), 3):
						var polygon: Array = []
						for corner in 3:
							var index := indices[triangle + corner]
							polygon.append({"p": original.global_transform * vertices[index], "n": (original.global_basis.inverse().transposed() * normals[index]).normalized(), "uv": uvs[index]})
						polygon = clip(polygon, 0, minimum.x, true)
						polygon = clip(polygon, 0, maximum.x, false)
						polygon = clip(polygon, 2, minimum.y, true)
						polygon = clip(polygon, 2, maximum.y, false)
						for corner in range(1, polygon.size() - 1):
							for point: Dictionary in [polygon[0], polygon[corner], polygon[corner + 1]]:
								output_vertices.append(point.p)
								output_normals.append(point.n)
								output_uvs.append(point.uv)
					if output_vertices.is_empty():
						continue
					var output := []
					output.resize(Mesh.ARRAY_MAX)
					output[Mesh.ARRAY_VERTEX] = output_vertices
					output[Mesh.ARRAY_NORMAL] = output_normals
					output[Mesh.ARRAY_TEX_UV] = output_uvs
					mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, output)
					mesh.surface_set_material(mesh.get_surface_count() - 1, original.get_active_material(surface))
				var chunk := MeshInstance3D.new()
				chunk.mesh = mesh
				group.add_child(chunk)
				chunk.global_transform = Transform3D.IDENTITY
				chunk.layers = original.layers
				chunk.cast_shadow = original.cast_shadow
				result += 1
		original.visible = false
	return result

static func clip(polygon: Array, axis: int, limit: float, keep_above: bool) -> Array:
	var result: Array = []
	if polygon.is_empty():
		return result
	var previous: Dictionary = polygon.back()
	var previous_inside: bool = previous.p[axis] >= limit if keep_above else previous.p[axis] <= limit
	for current: Dictionary in polygon:
		var inside: bool = current.p[axis] >= limit if keep_above else current.p[axis] <= limit
		if inside != previous_inside:
			var t: float = (limit - previous.p[axis]) / (current.p[axis] - previous.p[axis])
			result.append({"p": previous.p.lerp(current.p, t), "n": previous.n.lerp(current.n, t).normalized(), "uv": previous.uv.lerp(current.uv, t)})
		if inside:
			result.append(current)
		previous = current
		previous_inside = inside
	return result
