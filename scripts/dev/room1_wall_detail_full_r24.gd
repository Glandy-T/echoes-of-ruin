extends "res://scripts/dev/room1_pixel_unify_r22.gd"

# r24 is a review-only all-wall texture comparison.  r22 continues to own every
# other material.  This script owns precisely four texture uniforms.
const R24_ROOT := "res://assets/art/room1_wall_detail_full_r24/"
const R24_MAPS := {2:"wall_left.png",3:"wall_right.png",4:"wall_front.png",5:"wall_rear.png"}
const WALL_PARAMETERS := {2:"full_wall_left_map",3:"full_wall_right_map",4:"full_wall_front_map",5:"full_wall_rear_map"}
var r24_mode := 2 # 1 = r22 current, 2 = r24 complete PixelLab wall set.
var r24_map_snapshots:Array[Dictionary] = []
var r24_ready := false

func _build_door_glow() -> void:
	# r22 initializes its complete room first.  Capture only the four map
	# assignments after that, never live shader/pose/GI/light state.
	super._build_door_glow()
	_capture_r24_map_baseline()

func _capture_r24_map_baseline() -> void:
	if r24_ready:return
	for material:ShaderMaterial in complete_shell_materials:
		var kind:=int(material.get_shader_parameter("full_surface_kind"))
		if WALL_PARAMETERS.has(kind):
			var parameter:String=WALL_PARAMETERS[kind]
			r24_map_snapshots.append({"material":material,"kind":kind,"parameter":parameter,"map":material.get_shader_parameter(parameter)})
	r24_ready=true
	if _r24_assets_available():set_r24_mode(r24_mode)
	else:
		r24_mode=1
		_update_info()

func _r24_assets_available() -> bool:
	for name:String in R24_MAPS.values():
		if not ResourceLoader.exists(R24_ROOT+name):return false
	return r24_map_snapshots.size()>=4

func _restore_r24_maps() -> void:
	for item:Dictionary in r24_map_snapshots:
		(item.material as ShaderMaterial).set_shader_parameter(str(item.parameter),item.map)

func set_r24_mode(requested_mode:int) -> void:
	assert(r24_ready,"r24 wall baseline not initialized")
	r24_mode=clampi(requested_mode,1,2)
	_restore_r24_maps()
	if r24_mode==2:
		assert(_r24_assets_available(),"Missing r24 complete PixelLab wall textures")
		for item:Dictionary in r24_map_snapshots:
			(item.material as ShaderMaterial).set_shader_parameter(str(item.parameter),load(R24_ROOT+str(R24_MAPS[int(item.kind)])))
	_update_info()

func get_wall_detail_full_report() -> Dictionary:
	var maps:Dictionary={}
	for item:Dictionary in r24_map_snapshots:
		var texture:Texture2D=(item.material as ShaderMaterial).get_shader_parameter(str(item.parameter))
		maps[str(item.kind)]=texture.resource_path if texture else ""
	return {"mode":r24_mode,"walls":maps,"r22":get_pixel_unify_report(),"mutated_uniforms":["full_wall_left_map","full_wall_right_map","full_wall_front_map","full_wall_rear_map"]}

func _unhandled_key_input(event:InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1,KEY_2:set_r24_mode(int(event.physical_keycode-KEY_0))
			KEY_O:standard.toggle()
			KEY_H:info.get_parent().visible=not info.get_parent().visible
			_:super._unhandled_key_input(event);return
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if not info:return
	var label:="A r22 当前全墙" if r24_mode==1 else "B r24 PixelLab 全墙细节"
	info.text="Room 1 / 全墙细节 r24\n"+label+"；仅四面墙的贴图切换，地坪、20舱、门、灯带、玻璃、Shader、GI与布局保持r22\n1 r22当前 · 2 r24全墙 · O开盖 · H说明"
