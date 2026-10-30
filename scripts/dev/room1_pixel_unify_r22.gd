extends "res://scripts/dev/room1_complete_r19.gd"

# Review-only whole-room PixelLab material candidate.  r19 remains the formal
# entry and this script preserves its geometry, UVs, shaders, lights and GI.
const R22_ROOT := "res://assets/art/room1_pixel_unify_r22/"
const WALL_MAPS := {2:"wall_left.png",3:"wall_right.png",4:"wall_front.png",5:"wall_rear.png"}
const VARIANTS := ["a","b","c","d"]
var r22_mode := 2 # 1=r19 current, 2=r22 PixelLab material candidate.
var pixel_snapshots: Array[Dictionary] = []
var pixel_ready := false

func _build_door_glow() -> void:
	_super_build_door_glow()
	_capture_pixel_baseline()

func _super_build_door_glow() -> void:
	super._build_door_glow()

func _capture_pixel_baseline() -> void:
	if pixel_ready:return
	for material: ShaderMaterial in complete_shell_materials:
		_capture_material(material,"shell","")
	for id: String in room_pod_finishes:
		for entry: Dictionary in (room_pod_finishes[id] as RefCounted).entries:
			var role := str(entry.role)
			if role in ["lid","shell_side","shell_end"]:
				_capture_material(entry.material as ShaderMaterial,role,id)
	pixel_ready=true
	# During asset production, keep the review scene usable as an r19 baseline.
	# The candidate becomes the default automatically once its complete contract
	# exists; no placeholder maps are ever substituted.
	if _r22_assets_available():set_r22_mode(r22_mode)
	else:
		r22_mode=1
		_update_info()

func _capture_material(material: ShaderMaterial, role: String, pod_id: String) -> void:
	for item: Dictionary in pixel_snapshots:
		if item.material==material:return
	# r22 is a color-map review only.  Capturing every shader parameter here also
	# captured live pose/GI/screen/shadow values and later replayed them whenever
	# A/B changed.  Keep the baseline contract limited to parameters this review
	# actually mutates so a texture comparison can never change room state.
	var parameters:Dictionary={}
	if role=="shell":
		parameters.full_surface_mode=material.get_shader_parameter("full_surface_mode")
		var kind:=int(material.get_shader_parameter("full_surface_kind"))
		if kind==1:
			parameters.full_floor_aged_map=material.get_shader_parameter("full_floor_aged_map")
			parameters.full_floor_leaks_map=material.get_shader_parameter("full_floor_leaks_map")
		elif WALL_MAPS.has(kind):
			var map_parameter:String="full_wall_"+str(["","","left","right","front","rear"][kind])+"_map"
			parameters[map_parameter]=material.get_shader_parameter(map_parameter)
	else:
		parameters.color_map=material.get_shader_parameter("color_map")
	pixel_snapshots.append({"material":material,"role":role,"pod_id":pod_id,"parameters":parameters})

func _restore_pixel_baseline() -> void:
	for item: Dictionary in pixel_snapshots:
		var material:ShaderMaterial=item.material
		for key in item.parameters:material.set_shader_parameter(key,item.parameters[key])

func _require_r22_textures() -> void:
	for name: String in WALL_MAPS.values():assert(ResourceLoader.exists(R22_ROOT+name),"Missing r22 wall texture: "+R22_ROOT+name)
	for record: Dictionary in room_pod_records:
		var id:=str(record.id)
		for name in ["numbered/"+id+"_lid.png","numbered/"+id+"_shell_end.png","variant_"+VARIANTS[int(record.variant_index)]+"/shell_side.png"]:
			assert(ResourceLoader.exists(R22_ROOT+name),"Missing r22 pod texture: "+R22_ROOT+name)
	assert(ResourceLoader.exists(R22_ROOT+"floor_with_leaks.png"),"Missing r22 floor texture")

func _r22_assets_available() -> bool:
	if not ResourceLoader.exists(R22_ROOT+"floor_with_leaks.png"):return false
	for name:String in WALL_MAPS.values():
		if not ResourceLoader.exists(R22_ROOT+name):return false
	for record:Dictionary in room_pod_records:
		var id:=str(record.id)
		for name in ["numbered/"+id+"_lid.png","numbered/"+id+"_shell_end.png","variant_"+VARIANTS[int(record.variant_index)]+"/shell_side.png"]:
			if not ResourceLoader.exists(R22_ROOT+name):return false
	return true

func _r22_pod_path(item: Dictionary) -> String:
	var record:Dictionary=room_pod_records.filter(func(value):return str(value.id)==str(item.pod_id))[0]
	match str(item.role):
		"lid":return R22_ROOT+"numbered/"+str(item.pod_id)+"_lid.png"
		"shell_end":return R22_ROOT+"numbered/"+str(item.pod_id)+"_shell_end.png"
		"shell_side":return R22_ROOT+"variant_"+VARIANTS[int(record.variant_index)]+"/shell_side.png"
		_:assert(false,"Unexpected r22 material role");return ""

func set_r22_mode(requested_mode: int) -> void:
	assert(pixel_ready,"r22 material baseline not initialized")
	r22_mode=clampi(requested_mode,1,2)
	_restore_pixel_baseline()
	if r22_mode==1:
		_update_info()
		return
	_require_r22_textures()
	for item: Dictionary in pixel_snapshots:
		var material:ShaderMaterial=item.material
		if str(item.role)=="shell":
			var kind:=int(material.get_shader_parameter("full_surface_kind"))
			if kind==1:
				material.set_shader_parameter("full_surface_mode",3)
				material.set_shader_parameter("full_floor_aged_map",load(R22_ROOT+"floor_with_leaks.png"))
				material.set_shader_parameter("full_floor_leaks_map",load(R22_ROOT+"floor_with_leaks.png"))
			elif WALL_MAPS.has(kind):material.set_shader_parameter("full_surface_mode",3);material.set_shader_parameter("full_wall_"+["","","left","right","front","rear"][kind]+"_map",load(R22_ROOT+str(WALL_MAPS[kind])))
		else:material.set_shader_parameter("color_map",load(_r22_pod_path(item)))
	_update_info()

func get_pixel_unify_report() -> Dictionary:
	var result:Dictionary={"mode":r22_mode,"walls":{},"floor":"","pods":{},"shaders":{}}
	for item:Dictionary in pixel_snapshots:
		var material:ShaderMaterial=item.material
		if str(item.role)=="shell":
			var kind:=int(material.get_shader_parameter("full_surface_kind"))
			if kind==1:result.floor=(material.get_shader_parameter("full_floor_leaks_map") as Texture2D).resource_path
			elif WALL_MAPS.has(kind):result.walls[str(kind)]=(material.get_shader_parameter("full_wall_"+["","","left","right","front","rear"][kind]+"_map") as Texture2D).resource_path
		else:
			var key:=str(item.pod_id)+":"+str(item.role)
			result.pods[key]=(material.get_shader_parameter("color_map") as Texture2D).resource_path
		result.shaders[str(material.get_instance_id())]=material.shader.resource_path
	return result

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1:set_r22_mode(1)
			KEY_2:set_r22_mode(2)
			KEY_O:standard.toggle()
			KEY_H:info.get_parent().visible=not info.get_parent().visible
			_:super._unhandled_key_input(event);return
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if not info:return
	var label:="A 当前 r19" if r22_mode==1 else "B r22 整室 PixelLab 候选"
	info.text="Room 1 / 整室材质统一 r22\n"+label+"：四墙、连续地坪与20舱外壳；模型、布局、UV、灯、Shader 与 GI 保持\n1/A 当前材质 · 2/B PixelLab整室候选 · O开盖 · H说明"
