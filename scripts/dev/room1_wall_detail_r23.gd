extends "res://scripts/dev/room1_pixel_unify_r22.gd"

# r23 is a deliberately narrow material review.  It inherits r22 first, then
# changes *only* the rear-wall colour map on the two-panel test patch.
const R23_ROOT := "res://assets/art/room1_wall_detail_r23/"
const R23_MAPS := {
	1: "wall_rear_reference.png", # r13-density reference inside the fixed patch only
	3: "wall_rear_a.png",
	4: "wall_rear_b.png",
}
var r23_mode := 3
var rear_map_snapshots: Array[Dictionary] = []
var r23_ready := false

func _build_door_glow() -> void:
	super._build_door_glow()
	_capture_rear_map_baseline()

func _capture_rear_map_baseline() -> void:
	if r23_ready:return
	# The r22 constructor has already selected its complete whole-room candidate.
	# Capture only the one uniform that r23 owns; do not replay shader, pose, GI,
	# shadow, energy, or any other live state during a comparison.
	for material:ShaderMaterial in complete_shell_materials:
		if int(material.get_shader_parameter("full_surface_kind"))==5:
			rear_map_snapshots.append({"material":material,"map":material.get_shader_parameter("full_wall_rear_map")})
	r23_ready=true
	if _r23_assets_available():set_r23_mode(r23_mode)
	else:
		r23_mode=2
		_update_info()

func _r23_assets_available() -> bool:
	for name:String in R23_MAPS.values():
		if not ResourceLoader.exists(R23_ROOT+name):return false
	return not rear_map_snapshots.is_empty()

func _restore_rear_maps() -> void:
	for item:Dictionary in rear_map_snapshots:
		(item.material as ShaderMaterial).set_shader_parameter("full_wall_rear_map",item.map)

func set_r23_mode(requested_mode:int) -> void:
	assert(r23_ready,"r23 rear-wall baseline not initialized")
	r23_mode=clampi(requested_mode,1,4)
	_restore_rear_maps()
	if r23_mode!=2:
		assert(_r23_assets_available(),"Missing r23 rear-wall comparison texture")
		for item:Dictionary in rear_map_snapshots:
			(item.material as ShaderMaterial).set_shader_parameter("full_wall_rear_map",load(R23_ROOT+str(R23_MAPS[r23_mode])))
	_update_info()

func get_wall_detail_report() -> Dictionary:
	var rear_maps:Array[String]=[]
	for item:Dictionary in rear_map_snapshots:
		var texture:Texture2D=(item.material as ShaderMaterial).get_shader_parameter("full_wall_rear_map")
		rear_maps.append(texture.resource_path if texture else "")
	var r22:=get_pixel_unify_report()
	return {"mode":r23_mode,"rear_maps":rear_maps,"r22":r22,"mutated_uniforms":["full_wall_rear_map"],"patch_px":[944,16,1200,272],"patch_world":{"x":[12.0,15.2],"rear_z":-9.3}}

func _unhandled_key_input(event:InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1,KEY_2,KEY_3,KEY_4:set_r23_mode(int(event.physical_keycode-KEY_0))
			KEY_O:standard.toggle()
			KEY_H:info.get_parent().visible=not info.get_parent().visible
			_:super._unhandled_key_input(event);return
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if not info:return
	var labels:Dictionary={1:"A 旧墙材质密度参考（仅后墙PATCH）",2:"B r22 当前空白墙",3:"C PixelLab 新A",4:"D PixelLab 新B"}
	info.text="Room 1 / 后墙两板细节 r23\n"+str(labels[r23_mode])+"；只有后墙图固定PATCH变化，其他全室仍为r22\n1参考 · 2当前 · 3新A · 4新B · O开盖 · H说明"
