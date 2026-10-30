extends "res://scripts/dev/room1_wall_detail_full_r24.gd"

# r25 is a deliberately narrow floor-material review. r24 remains fixed so the
# comparison cannot accidentally compare the prior sparse wall set.
const R25_ROOT := "res://assets/art/room1_floor_detail_r25/"
const R25_MAPS := {
	2: "floor_reference.png", # r15-density reference only inside the fixed patch
	3: "floor_candidate.png", # new PixelLab candidate only inside the fixed patch
}
const PATCH_PX := Rect2i(168,96,256,256)
var r25_mode := 3
var r25_floor_snapshots:Array[Dictionary] = []
var r25_ready := false

func _build_door_glow() -> void:
	super._build_door_glow()
	_capture_r25_floor_baseline()

func _capture_r25_floor_baseline() -> void:
	if r25_ready:return
	for material:ShaderMaterial in complete_shell_materials:
		if int(material.get_shader_parameter("full_surface_kind"))==1:
			r25_floor_snapshots.append({"material":material,"aged":material.get_shader_parameter("full_floor_aged_map"),"leaks":material.get_shader_parameter("full_floor_leaks_map")})
	r25_ready=true
	# Keep the wall material set locked to r24 for every floor mode.
	set_r24_mode(2)
	if _r25_assets_available():set_r25_mode(r25_mode)
	else:
		r25_mode=1
		_update_info()

func _r25_assets_available() -> bool:
	for name:String in R25_MAPS.values():
		if not ResourceLoader.exists(R25_ROOT+name):return false
	return not r25_floor_snapshots.is_empty()

func _restore_r25_floor_maps() -> void:
	for item:Dictionary in r25_floor_snapshots:
		(item.material as ShaderMaterial).set_shader_parameter("full_floor_aged_map",item.aged)
		(item.material as ShaderMaterial).set_shader_parameter("full_floor_leaks_map",item.leaks)

func set_r25_mode(requested_mode:int) -> void:
	assert(r25_ready,"r25 floor baseline not initialized")
	r25_mode=clampi(requested_mode,1,3)
	_restore_r25_floor_maps()
	set_r24_mode(2)
	if r25_mode>1:
		assert(_r25_assets_available(),"Missing r25 local floor comparison texture")
		var map:Texture2D=load(R25_ROOT+str(R25_MAPS[r25_mode]))
		for item:Dictionary in r25_floor_snapshots:
			(item.material as ShaderMaterial).set_shader_parameter("full_floor_aged_map",map)
			(item.material as ShaderMaterial).set_shader_parameter("full_floor_leaks_map",map)
	_update_info()

func get_floor_detail_report() -> Dictionary:
	var maps:Array[String]=[]
	for item:Dictionary in r25_floor_snapshots:
		var texture:Texture2D=(item.material as ShaderMaterial).get_shader_parameter("full_floor_leaks_map")
		maps.append(texture.resource_path if texture else "")
	return {"mode":r25_mode,"floor_maps":maps,"patch_px":[PATCH_PX.position.x,PATCH_PX.position.y,PATCH_PX.size.x,PATCH_PX.size.y],"world_patch":{"x":[2.3,5.5],"z":[-8.1,-4.9]},"r24":get_wall_detail_full_report(),"mutated_uniforms":["full_floor_aged_map","full_floor_leaks_map"]}

func _unhandled_key_input(event:InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1,KEY_2,KEY_3:set_r25_mode(int(event.physical_keycode-KEY_0))
			KEY_O:standard.toggle()
			KEY_H:info.get_parent().visible=not info.get_parent().visible
			_:super._unhandled_key_input(event);return
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if not info:return
	var labels:Dictionary={1:"A r22 当前地坪",2:"B r15 原密度局部参考",3:"C PixelLab 新局部候选"}
	info.text="Room 1 / 地坪细节局部 r25\n"+str(labels[r25_mode])+"；只替换固定256px地坪补丁，r24全墙、20舱、门、灯光、GI和布局不变\n1 当前 · 2 原密度参考 · 3 PixelLab候选 · O开盖 · H说明"
