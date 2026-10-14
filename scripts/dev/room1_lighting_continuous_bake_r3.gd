@tool
extends "res://scripts/dev/room1_lighting_shadow_test_r2.gd"

@export_range(0.0, 2.0) var continuous_baked_energy := 1.2
var baked_receivers: Array[ShaderMaterial] = []
var continuous_ready := false
@export_file("*.glb") var baked_geometry_path := "res://assets/art/room1_continuous_bake_r3/room1_baked_uv2_r3.glb"

func _build_strip_lights() -> void:
	# No point or spot lights for the ribbon in this version.
	pass

func _ready() -> void:
	super._ready()
	var chunks := $Shell.get_node_or_null("FloorLightChunks")
	if chunks:
		chunks.queue_free()
	$Shell.find_child("Floor_continuous_no_tile_seams", true, false).visible = true
	var copy := (load(baked_geometry_path) as PackedScene).instantiate()
	add_child(copy)
	copy.visible = false
	var original_mapping: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/art/room1_continuous_bake_r3/mesh_mapping.json"))
	var mapping := {}
	for key: String in original_mapping:
		var record: Dictionary = original_mapping[key].duplicate()
		record.mesh = str(record.mesh).replace(".", "_")
		mapping[key.replace(".", "_")] = record
	var irradiance := load("res://assets/art/room1_continuous_bake_r3/strip_irradiance_denoised.exr") as Texture2D
	assert(irradiance != null and irradiance.get_width() == 2048)
	for node: MeshInstance3D in copy.find_children("*", "MeshInstance3D", true, false):
		if not mapping.has(str(node.name)):
			continue
		var record: Dictionary = mapping[str(node.name)]
		if record.mesh in ["pod_v3_glass", "pod_v3_display"]:
			continue
		var group: Node = $Shell if record.group == "Shell" else get_node("Pods/" + str(record.group))
		var receiver := group.find_child(str(record.mesh), true, false) as MeshInstance3D
		assert(receiver != null)
		var materials: Array[ShaderMaterial] = []
		for surface in receiver.mesh.get_surface_count():
			var source := receiver.get_active_material(surface) as ShaderMaterial
			var material := ShaderMaterial.new()
			material.shader = preload("res://scripts/dev/room1_baked_strip_receiver_r3.gdshader")
			if source:
				for parameter in ["color_map", "base_color", "emission_map", "has_emission_map"]:
					material.set_shader_parameter(parameter, source.get_shader_parameter(parameter))
			else:
				var original := receiver.get_active_material(surface) as BaseMaterial3D
				material.set_shader_parameter("color_map", original.albedo_texture if original.albedo_texture else _solid_texture(Color.WHITE))
				material.set_shader_parameter("base_color", original.albedo_color)
				material.set_shader_parameter("emission_map", _solid_texture(Color.BLACK))
			material.set_shader_parameter("strip_irradiance", irradiance)
			materials.append(material)
			baked_receivers.append(material)
		receiver.mesh = node.mesh
		receiver.global_transform = node.global_transform
		for surface in receiver.mesh.get_surface_count():
			receiver.set_surface_override_material(surface, materials[mini(surface, materials.size() - 1)])
	copy.queue_free()
	continuous_ready = true
	apply_sample_state()

func apply_sample_state() -> void:
	super.apply_sample_state()
	if continuous_ready:
		for material in baked_receivers:
			material.set_shader_parameter("baked_energy", continuous_baked_energy if strip_on else 0.0)
			material.set_shader_parameter("strip_surface_energy", strip_surface_energy if strip_on else 0.0)
	_update_info()

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 连续灯带烘焙 r3 · 待审\nWASD移动 · 1–9位置 · R复位 · T标记 · H说明\nL整条灯带 %s · G舱内光 · B屏幕 · N光晕\n灯带为连续发光面，0个点光/聚光代理；静态阴影已烘焙。" % strip_on
