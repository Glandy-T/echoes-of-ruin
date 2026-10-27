extends "res://scripts/dev/room1_pod_room_v5.gd"
const SIDE_LIGHT := preload("res://scripts/dev/room1_pod_side_lights_v7.gdshader")
const TUBE_SURFACE := preload("res://scripts/dev/room1_pod_tube_emitter_v7.gdshader")
const FIXTURES := preload("res://scenes/dev/room1_pod_inner_tubes_v7.tscn")
var tube_materials: Array[ShaderMaterial]=[]
var side_light_materials: Array[ShaderMaterial]=[]
var side_tubes_enabled:=true

func _ready() -> void:
	super._ready()
	for item in pod_materials:
		var material:ShaderMaterial=item.material
		if material.shader.resource_path=="res://scripts/dev/room1_window_interior_lighting_r2.gdshader":
			var parameters:=_copy_parameters(material)
			material.shader=SIDE_LIGHT
			for key in parameters:material.set_shader_parameter(key,parameters[key])
			side_light_materials.append(material)
	for pose in pod_candidates:
		var model:Node3D=pod_candidates[pose]
		# Separate, editable component on the fixed shell, beneath its lip.
		var fixtures:=FIXTURES.instantiate();model.add_child(fixtures)
		for tube:MeshInstance3D in fixtures.find_children("InnerTube_*","MeshInstance3D",true,false):
			var material:=tube.material_override.duplicate() as ShaderMaterial
			tube.material_override=material;tube_materials.append(material)
	apply_sample_state()

func apply_sample_state() -> void:
	super.apply_sample_state()
	if not pod_room_ready:return
	# Remove the legacy head-centred Omni as well as the old point falloff.
	window_proxies["P12"].visible=false
	window_proxies["P12"].light_energy=0.0
	var power:=1.0 if side_tubes_enabled and windows_on and local_light_on else 0.0
	for material in side_light_materials:
		material.set_shader_parameter("chamber_from_world",$Pods/P12.global_transform.affine_inverse())
		material.set_shader_parameter("tube_powered",power)
	for material in tube_materials:material.set_shader_parameter("tube_powered",power)
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode==KEY_U:
		side_tubes_enabled=not side_tubes_enabled;apply_sample_state()
		get_viewport().set_input_as_handled();return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		info.text="Room 1 / 舱内两侧灯管 v7\nO开/关盖 · U两侧灯管 · G舱内灯 · T玻璃显隐 · J回位 · WASD\n取消中央点光；两条长边内嵌低亮度灯管，玻璃与房间其他照明保持。"
