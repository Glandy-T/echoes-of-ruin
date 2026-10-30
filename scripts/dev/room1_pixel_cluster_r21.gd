extends "res://scripts/dev/room1_complete_r19.gd"

# Review-only r21 material comparison.  It deliberately retains r19's shaders,
# lightmaps, lighting and geometry; only four PixelLab color maps are swapped.
const R20_ROOT := "res://assets/art/room1_pixel_cluster_r20/"
const R21_ROOT := "res://assets/art/room1_pixel_cluster_r21/"
const MAP_NAMES := {"wall": "wall_left.png", "lid": "pod_lid.png", "shell_side": "pod_shell_side.png", "shell_end": "pod_shell_end.png"}
var cluster_mode := 3 # 1=r19, 2=r20 PixelLab maps, 3=r21 PixelLab maps.
var cluster_snapshots: Array[Dictionary] = []
var cluster_ready := false

func _build_door_glow() -> void:
	super._build_door_glow()
	_capture_cluster_baseline()

func _capture_cluster_baseline() -> void:
	if cluster_ready:return
	for material: ShaderMaterial in complete_shell_materials:
		if int(material.get_shader_parameter("full_surface_kind")) == 2:_capture_material(material, "wall")
	for entry: Dictionary in (room_pod_finishes["P12"] as RefCounted).entries:
		var role := str(entry.role)
		if MAP_NAMES.has(role):_capture_material(entry.material as ShaderMaterial, role)
	cluster_ready=true
	set_cluster_mode(cluster_mode)

func _capture_material(material: ShaderMaterial, role: String) -> void:
	for item: Dictionary in cluster_snapshots:
		if item.material == material:return
	cluster_snapshots.append({"material":material,"role":role,"shader":material.shader,"parameters":_copy_parameters(material)})

func _restore_cluster_baseline() -> void:
	for item: Dictionary in cluster_snapshots:
		var material:ShaderMaterial=item.material
		material.shader=item.shader
		for key in item.parameters:material.set_shader_parameter(key,item.parameters[key])

func _root_for_mode() -> String:
	return R20_ROOT if cluster_mode == 2 else R21_ROOT

func _require_review_textures(root: String) -> void:
	for name: String in MAP_NAMES.values():assert(ResourceLoader.exists(root+name),"Missing PixelLab r21 review texture: "+root+name)

func set_cluster_mode(requested_mode: int) -> void:
	assert(cluster_ready,"r21 review baseline was not initialized.")
	cluster_mode=clampi(requested_mode,1,3)
	_restore_cluster_baseline()
	if cluster_mode == 1:
		_update_info()
		return
	var root := _root_for_mode()
	_require_review_textures(root)
	for item: Dictionary in cluster_snapshots:
		var material:ShaderMaterial=item.material
		var role := str(item.role)
		# Keep each r19/v8 shader and every original parameter.  This is strictly a
		# color-map comparison, not r20's former lighting/value-shader experiment.
		if role == "wall": material.set_shader_parameter("full_wall_left_map",load(root+MAP_NAMES.wall))
		else: material.set_shader_parameter("color_map",load(root+MAP_NAMES[role]))
	_update_info()

func get_cluster_review_report() -> Dictionary:
	var pod_maps := {}
	var pod_shaders := {}
	var wall_maps := []
	var wall_shaders := []
	for item: Dictionary in cluster_snapshots:
		var material:ShaderMaterial=item.material
		var role := str(item.role)
		if role == "wall":
			var wall_map:Texture2D=material.get_shader_parameter("full_wall_left_map")
			wall_maps.append(wall_map.resource_path)
			wall_shaders.append(material.shader.resource_path)
		else:
			var pod_map:Texture2D=material.get_shader_parameter("color_map")
			pod_maps[role]=pod_map.resource_path
			pod_shaders[role]=material.shader.resource_path
	return {"mode":cluster_mode,"pod_maps":pod_maps,"wall_maps":wall_maps,"pod_shaders":pod_shaders,"wall_shaders":wall_shaders}

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1:set_cluster_mode(1)
			KEY_2:set_cluster_mode(2)
			KEY_3:set_cluster_mode(3)
			KEY_O:standard.toggle()
			KEY_H:info.get_parent().visible=not info.get_parent().visible
			_:super._unhandled_key_input(event);return
		get_viewport().set_input_as_handled();return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if not info:return
	var label: String = ["","A 原 r19 贴图","B r20 PixelLab 贴图（原光照）","C r21 PixelLab 强化像素块面（原光照）"][cluster_mode]
	info.text="Room 1 / 局部像素尺度 r21\n"+label+"：左墙原图范围与 P12 三块外壳；模型、布局、UV、Shader、光照与 GI 保持\n1/A 原版 · 2/B 上轮材质 · 3/C 本轮材质 · O开盖 · H说明"
