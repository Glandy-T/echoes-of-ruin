extends "res://scripts/dev/cryo_corridor_sample_v1.gd"

const BAKED_MODEL := preload("res://assets/art/cryo_corridor_baked_v2/corridor_baked_v2.glb")
const BAKED_SHADER := preload("res://scripts/dev/cryo_corridor_baked_surface_v2.gdshader")
const GHOST_SHADER := preload("res://scripts/dev/cryo_corridor_baked_ghost_v2.gdshader")
const LIGHT_ROOT := "res://assets/art/cryo_corridor_baked_v2/"
var baked_materials: Array[ShaderMaterial] = []
var raw_corridor_light := false

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint():return
	var old := corridor_sample
	for i in range(occluders.size()-1,-1,-1):
		if old.is_ancestor_of(occluders[i].mesh):occluders.remove_at(i)
	old.visible=false
	corridor_sample=BAKED_MODEL.instantiate()
	corridor_sample.name="CorridorBakedV2"
	add_child(corridor_sample)
	for item in corridor_sample.find_children("*","MeshInstance3D",true,false):
		var mesh := item as MeshInstance3D
		mesh.layers=1 | SAMPLE_LAYER
		var wall := "Wall" in str(mesh.name)
		var mat := ShaderMaterial.new()
		mat.shader=BAKED_SHADER
		mat.set_shader_parameter("lamp_power",1.0)
		mat.set_shader_parameter("baked_energy",1.2)
		mat.set_shader_parameter("color_map",load("res://assets/art/cryo_corridor_sample_v1/"+("wall.png" if wall else "floor.png")))
		mat.set_shader_parameter("emission_map",load("res://assets/art/cryo_corridor_sample_v1/wall_emission.png"))
		mat.set_shader_parameter("is_wall",1.0 if wall else 0.0)
		mat.set_shader_parameter("irradiance_map",load(LIGHT_ROOT+"strip_irradiance_denoised.exr"))
		mesh.material_override=mat
		baked_materials.append(mat)
		if wall:
			var ghost := mat.duplicate() as ShaderMaterial
			ghost.shader=GHOST_SHADER
			baked_materials.append(ghost)
			occluders.append({"mesh":mesh,"originals":[mat],"faded":[ghost],"active":false,"override":mat})
	old.queue_free()
	sample_lights.visible=false
	_update_info()

func set_sample_visible(enabled: bool) -> void:
	super.set_sample_visible(enabled)
	sample_lights.visible=false

func set_corridor_lamps(enabled: bool) -> void:
	corridor_lamps_on=enabled
	if sample_lights:sample_lights.visible=false
	for mat in baked_materials:mat.set_shader_parameter("lamp_power",1.0 if enabled else 0.0)

func set_corridor_raw(enabled: bool) -> void:
	raw_corridor_light=enabled
	var texture := load(LIGHT_ROOT+("strip_irradiance.exr" if enabled else "strip_irradiance_denoised.exr"))
	for mat in baked_materials:mat.set_shader_parameter("irradiance_map",texture)
	_update_info()

func _update_info() -> void:
	super._update_info()
	if info:info.text="4F走廊烘焙 v2 / "+("raw" if raw_corridor_light else "denoised")+"\nE 门认证 · F8 小样 · F9 灯带 · F10 raw/降噪。两侧墙板＋地坪为配套烘焙，实时补光关闭。"

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode==KEY_F10:
		set_corridor_raw(not raw_corridor_light)
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)
