extends "res://scripts/dev/room1_complete_r19.gd"

# Review-only local material experiment. It never alters geometry, UVs,
# collision, camera, light locations or the formal r19 scene.
const REVIEW_ROOT := "res://assets/art/room1_pixel_cluster_r20/"
const WALL_SHADER := preload("res://scripts/dev/room1_pixel_cluster_wall_r20.gdshader")
const POD_SHADER := preload("res://scripts/dev/room1_pixel_cluster_pod_r20.gdshader")
const WALL_TEXTURE := REVIEW_ROOT+"wall_left.png"
const POD_TEXTURES := {"lid": REVIEW_ROOT+"pod_lid.png", "shell_side": REVIEW_ROOT+"pod_shell_side.png", "shell_end": REVIEW_ROOT+"pod_shell_end.png"}
var cluster_mode := 1 # A=r19, B=PixelLab clusters, C=B plus gentle value grouping.
var cluster_snapshots: Array[Dictionary] = []
var cluster_ready := false

func _build_door_glow() -> void:
	super._build_door_glow()
	_capture_cluster_baseline()

func _capture_cluster_baseline() -> void:
	if cluster_ready:return
	for material: ShaderMaterial in complete_shell_materials:
		if int(material.get_shader_parameter("full_surface_kind")) == 2:_capture_material(material)
	for entry: Dictionary in (room_pod_finishes["P12"] as RefCounted).entries:
		if str(entry.role) in POD_TEXTURES:_capture_material(entry.material as ShaderMaterial)
	cluster_ready=true
	set_cluster_mode(1)

func _capture_material(material: ShaderMaterial) -> void:
	for item: Dictionary in cluster_snapshots:
		if item.material == material:return
	cluster_snapshots.append({"material":material,"shader":material.shader,"parameters":_copy_parameters(material)})

func _restore_cluster_baseline() -> void:
	for item: Dictionary in cluster_snapshots:
		var material: ShaderMaterial=item.material
		material.shader=item.shader
		for key in item.parameters:material.set_shader_parameter(key,item.parameters[key])

func _apply_cluster_shader(item: Dictionary, shader: Shader, value_mode: int) -> void:
	var material: ShaderMaterial=item.material
	material.shader=shader
	for key in item.parameters:material.set_shader_parameter(key,item.parameters[key])
	material.set_shader_parameter("local_sample_mode",value_mode)

func _require_review_textures() -> void:
	for path: String in [WALL_TEXTURE,POD_TEXTURES.lid,POD_TEXTURES.shell_side,POD_TEXTURES.shell_end]:assert(ResourceLoader.exists(path),"Missing PixelLab r20 review texture: "+path)

func set_cluster_mode(requested_mode: int) -> void:
	assert(cluster_ready,"r20 review baseline was not initialized.")
	cluster_mode=clampi(requested_mode,1,3)
	_restore_cluster_baseline()
	if cluster_mode==1:_update_info();return
	_require_review_textures()
	var value_mode:=1 if cluster_mode==3 else 0
	for item: Dictionary in cluster_snapshots:
		var material: ShaderMaterial=item.material
		var old_shader: Shader=item.shader
		if old_shader.resource_path=="res://scripts/dev/room1_complete_surface_r19.gdshader":
			_apply_cluster_shader(item,WALL_SHADER,value_mode)
			material.set_shader_parameter("full_wall_left_map",load(WALL_TEXTURE))
		else:
			_apply_cluster_shader(item,POD_SHADER,value_mode)
			var role:=""
			for entry: Dictionary in (room_pod_finishes["P12"] as RefCounted).entries:
				if entry.material==material:role=str(entry.role);break
			assert(POD_TEXTURES.has(role),"Unexpected r20 P12 material role.")
			material.set_shader_parameter("color_map",load(str(POD_TEXTURES[role])))
	_update_info()

func get_cluster_review_report() -> Dictionary:
	var finish: RefCounted=room_pod_finishes["P12"]
	var material_paths:= {}
	for entry: Dictionary in finish.entries:
		if str(entry.role) in POD_TEXTURES:material_paths[str(entry.role)]=(entry.material as ShaderMaterial).get_shader_parameter("color_map").resource_path
	var wall_paths:=[]
	for material: ShaderMaterial in complete_shell_materials:
		if int(material.get_shader_parameter("full_surface_kind"))==2:wall_paths.append((material.get_shader_parameter("full_wall_left_map") as Texture2D).resource_path)
	return {"mode":cluster_mode,"pod_maps":material_paths,"wall_maps":wall_paths}

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
	var label: String = ["","A 原 r19","B PixelLab 像素簇","C B＋分段明暗"][cluster_mode]
	info.text="Room 1 / 局部像素尺度 r20\n"+label+"：左墙两块墙板／3.2m样段与 P12 三块外壳；模型、布局、UV、灯位、GI 保持\n1/A 原版 · 2/B PixelLab颗粒 · 3/C PixelLab＋温和明暗分段 · O开盖 · H说明"
