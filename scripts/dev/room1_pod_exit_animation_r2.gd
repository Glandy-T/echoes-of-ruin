@tool
extends "res://scripts/dev/room1_pod_exit_animation_r1.gd"
var interior_window_materials: Dictionary = {}
func _window_effect_pods() -> PackedStringArray:
	return PackedStringArray(["P02", "P17"])

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():
		return
	for id in _window_effect_pods():
		room_glass_shaders[id].shader = preload("res://scripts/dev/room1_glass_chamber_transmission_r2.gdshader")
		room_glass_shaders[id].set_shader_parameter("chamber_light_position", window_proxies[id].global_position)
		var materials: Array[ShaderMaterial] = []
		for mesh_name in ["pod_v3_interior", "pod_v3_interior_001", "pod_v3_mattress"]:
			var mesh := get_node("Pods/" + id).find_child(mesh_name, true, false) as MeshInstance3D
			for surface in mesh.mesh.get_surface_count():
				var material := mesh.get_active_material(surface).duplicate() as ShaderMaterial
				material.shader = preload("res://scripts/dev/room1_window_interior_lighting_r2.gdshader")
				material.set_shader_parameter("window_light_position", window_proxies[id].global_position)
				mesh.set_surface_override_material(surface, material)
				materials.append(material)
				baked_receivers.append(material)
		interior_window_materials[id] = materials
	apply_sample_state()
func apply_sample_state() -> void:
	super.apply_sample_state()
	for id in interior_window_materials:
		room_glass_shaders[id].set_shader_parameter("chamber_powered", 1.0 if windows_on and local_light_on and window_lit_pods.has(id) else 0.0)
		for material in interior_window_materials[id]:
			material.set_shader_parameter("window_powered", 1.0 if windows_on and local_light_on and window_lit_pods.has(id) else 0.0)
