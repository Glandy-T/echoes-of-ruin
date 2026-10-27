extends "res://scripts/dev/room1_floor_palette_r9.gd"

const POD_ROOT := "res://assets/art/room1_pod_room_v5/"
const NEW_GLASS := preload("res://scripts/dev/room1_pod_volume_glass_v4.gdshader")
var pod_candidates: Dictionary = {}
var pod_materials: Array[Dictionary] = []
var pod_glass: Array[MeshInstance3D] = []
var pod_screens: Array[ShaderMaterial] = []
var pod_bloom: Dictionary = {}
var original_bloom_occluders: Array[MeshInstance3D] = []
var original_bloom_screen: MeshInstance3D
var original_bloom_mesh: Mesh
var original_bloom_transform: Transform3D
var original_bloom_pixels: Texture2D
var revised_pod := true
var open_pod := true
var pane_visible := true
var pod_room_ready := false

func _ready() -> void:
	super._ready()
	var original: Node3D = $Pods/P12
	var bloom_world: Node3D = bloom_camera.get_parent()
	for node in bloom_world.get_children():
		if not node is MeshInstance3D: continue
		if node.is_queued_for_deletion(): continue
		if node == bloom_actor: continue
		if node.material_override == room_bloom_materials["P12"]:
			original_bloom_screen = node
			original_bloom_mesh = node.mesh
			original_bloom_transform = node.global_transform
		elif node.global_position.distance_to(original.global_position) < 1.5:
			original_bloom_occluders.append(node)
	original_bloom_pixels = room_bloom_materials["P12"].get_shader_parameter("screen_pixels")
	for pose in ["closed", "open"]:
		var model := (load(POD_ROOT+"pod_"+pose+"_v5.glb") as PackedScene).instantiate() as Node3D
		$Pods.add_child(model)
		model.name = "P12_v5_"+pose
		model.global_transform = original.global_transform
		pod_candidates[pose] = model
		_install_pod_materials(model, pose)
		var clones: Array[MeshInstance3D] = []
		var black := StandardMaterial3D.new()
		black.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		black.albedo_color = Color.BLACK
		black.cull_mode = BaseMaterial3D.CULL_DISABLED
		for mesh: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
			if str(mesh.name).contains("glass") or str(mesh.name).contains("display"): continue
			var clone := MeshInstance3D.new()
			clone.mesh = mesh.mesh
			clone.material_override = black
			bloom_world.add_child(clone)
			clone.global_transform = mesh.global_transform
			clones.append(clone)
		pod_bloom[pose] = clones
	pod_room_ready = true
	set_pod_candidate(true, true)
	call_deferred("position_structure_review")

func _install_pod_materials(model: Node3D, pose: String) -> void:
	var exterior := ($Pods/P12.find_child("pod_v3_shell_side",true,false) as MeshInstance3D).get_active_material(0) as ShaderMaterial
	var inside := ($Pods/P12.find_child("pod_v3_interior",true,false) as MeshInstance3D).get_active_material(0) as ShaderMaterial
	var irradiance := load(POD_ROOT+pose+"_irradiance.exr") as Texture2D
	assert(irradiance != null)
	for mesh: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		for surface in mesh.mesh.get_surface_count():
			var source := mesh.get_active_material(surface) as BaseMaterial3D
			assert(source != null)
			var key := source.resource_name.to_lower()
			var material: ShaderMaterial
			if key.contains("glass"):
				material = ShaderMaterial.new()
				material.shader = NEW_GLASS
				material.set_shader_parameter("glass_pixels", source.albedo_texture)
				mesh.layers = 2
				mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				pod_glass.append(mesh)
			elif key.contains("display"):
				material = room_screen_shaders["P12"].duplicate() as ShaderMaterial
				material.set_shader_parameter("screen_pixels", source.albedo_texture)
				mesh.layers = 4
				pod_screens.append(material)
			else:
				material = (inside if key.contains("interior") or key.contains("mattress") else exterior).duplicate() as ShaderMaterial
				material.set_shader_parameter("color_map", source.albedo_texture)
				material.set_shader_parameter("base_color", source.albedo_color)
				material.set_shader_parameter("has_emission_map", 0.0)
				material.set_shader_parameter("strip_irradiance", irradiance)
				pod_materials.append({"material": material,"irradiance": irradiance})
				baked_receivers.append(material)
			mesh.set_surface_override_material(surface, material)

func set_pod_candidate(enabled: bool, opened: bool) -> void:
	revised_pod = enabled
	open_pod = opened
	if not pod_room_ready: return
	$Pods/P12.visible = not enabled
	for pose in pod_candidates:
		pod_candidates[pose].visible = enabled and pose == ("open" if opened else "closed")
		for clone: MeshInstance3D in pod_bloom[pose]: clone.visible = pod_candidates[pose].visible
	for mesh in original_bloom_occluders: mesh.visible = not enabled
	if original_bloom_screen:
		if enabled:
			var model: Node3D = pod_candidates["open" if opened else "closed"]
			for mesh: MeshInstance3D in model.find_children("*", "MeshInstance3D",true,false):
				if str(mesh.name).contains("display"):
					original_bloom_screen.mesh = mesh.mesh
					original_bloom_screen.global_transform = mesh.global_transform
					room_bloom_materials["P12"].set_shader_parameter("screen_pixels",(mesh.get_active_material(0) as ShaderMaterial).get_shader_parameter("screen_pixels"))
		else:
			original_bloom_screen.mesh = original_bloom_mesh
			original_bloom_screen.global_transform = original_bloom_transform
			room_bloom_materials["P12"].set_shader_parameter("screen_pixels", original_bloom_pixels)
	set_pane_visible(pane_visible)
	apply_sample_state()

func set_pane_visible(enabled: bool) -> void:
	pane_visible = enabled
	for mesh in pod_glass: mesh.visible = enabled
	_update_info()

func set_surface_lighting(enabled: bool) -> void:
	super.set_surface_lighting(enabled)
	for item in pod_materials: item.material.set_shader_parameter("strip_irradiance", item.irradiance)

func apply_sample_state() -> void:
	super.apply_sample_state()
	if not pod_room_ready: return
	for item in pod_materials:
		item.material.set_shader_parameter("window_light_position", window_proxies["P12"].global_position)
		item.material.set_shader_parameter("window_powered", 1.0 if windows_on and local_light_on else 0.0)
	for material in pod_screens: material.set_shader_parameter("powered", 1.0 if screens_on else 0.0)
	for mesh in pod_glass:
		(mesh.get_active_material(0) as ShaderMaterial).set_shader_parameter("reflections_enabled", 1.0 if reflection_on else 0.0)
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_V: set_pod_candidate(not revised_pod, open_pod)
			KEY_O: set_pod_candidate(revised_pod, not open_pod)
			KEY_T: set_pane_visible(not pane_visible)
			_: super._unhandled_key_input(event); return
		get_viewport().set_input_as_handled()

func _update_info() -> void:
	if info:
		info.text = "Room 1 / v4单舱实际房间光照 v5 · %s · %s\nV旧/新 · O关/开 · T玻璃显隐 · G舱内光 · L灯带 · N固有色 · J回位 · WASD\n只换P12；房间灯光/镜头/其余19舱保持，新舱两姿态各用独立UV2受光。" % ["新v4" if revised_pod else "原v3开盖", "45°开盖" if open_pod else "闭合"]
