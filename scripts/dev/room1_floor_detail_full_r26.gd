extends "res://scripts/dev/room1_floor_detail_r25.gd"

# r26 promotes the user-approved r25 C language to a full, independently
# authored PixelLab floor. r25 C remains available as the comparison baseline.
const R26_ROOT := "res://assets/art/room1_floor_detail_full_r26/"
const R26_MAP := "floor_with_leaks.png"
var r26_mode := 2 # 1 = approved r25 C patch, 2 = full r26 floor.
var r26_floor_snapshots:Array[Dictionary] = []
var r26_ready := false

func _build_door_glow() -> void:
	super._build_door_glow()
	_capture_r26_floor_baseline()

func _capture_r26_floor_baseline() -> void:
	if r26_ready:return
	for material:ShaderMaterial in complete_shell_materials:
		if int(material.get_shader_parameter("full_surface_kind"))==1:
			r26_floor_snapshots.append({"material":material,"aged":material.get_shader_parameter("full_floor_aged_map"),"leaks":material.get_shader_parameter("full_floor_leaks_map")})
	r26_ready=true
	set_r25_mode(3) # Approved r25 C and r24 walls are the starting material state.
	if _r26_assets_available():set_r26_mode(r26_mode)
	else:
		r26_mode=1
		_update_info()

func _r26_assets_available() -> bool:
	return ResourceLoader.exists(R26_ROOT+R26_MAP) and not r26_floor_snapshots.is_empty()

func _restore_r26_floor_maps() -> void:
	for item:Dictionary in r26_floor_snapshots:
		(item.material as ShaderMaterial).set_shader_parameter("full_floor_aged_map",item.aged)
		(item.material as ShaderMaterial).set_shader_parameter("full_floor_leaks_map",item.leaks)

func set_r26_mode(requested_mode:int) -> void:
	assert(r26_ready,"r26 floor baseline not initialized")
	r26_mode=clampi(requested_mode,1,2)
	_restore_r26_floor_maps()
	set_r25_mode(3)
	if r26_mode==2:
		assert(_r26_assets_available(),"Missing r26 complete floor texture")
		var map:Texture2D=load(R26_ROOT+R26_MAP)
		for item:Dictionary in r26_floor_snapshots:
			(item.material as ShaderMaterial).set_shader_parameter("full_floor_aged_map",map)
			(item.material as ShaderMaterial).set_shader_parameter("full_floor_leaks_map",map)
	_update_info()

func get_floor_detail_full_report() -> Dictionary:
	var maps:Array[String]=[]
	for item:Dictionary in r26_floor_snapshots:
		var texture:Texture2D=(item.material as ShaderMaterial).get_shader_parameter("full_floor_leaks_map")
		maps.append(texture.resource_path if texture else "")
	return {"mode":r26_mode,"floor_maps":maps,"r25":get_floor_detail_report(),"mutated_uniforms":["full_floor_aged_map","full_floor_leaks_map"]}

func _unhandled_key_input(event:InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1,KEY_2:set_r26_mode(int(event.physical_keycode-KEY_0))
			KEY_O:standard.toggle()
			KEY_H:info.get_parent().visible=not info.get_parent().visible
			_:super._unhandled_key_input(event);return
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if not info:return
	var label:="A r25 已认可局部" if r26_mode==1 else "B r26 PixelLab 全地坪"
	info.text="Room 1 / 全地坪细节 r26\n"+label+"；仅切换两张既有地板颜色图绑定，r24全墙、20舱、门、灯光、GI和布局不变\n1 r25局部 · 2 r26全地坪 · O开盖 · H说明"
