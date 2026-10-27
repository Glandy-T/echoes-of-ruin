extends Node3D

const OLD_CLOSED := preload("res://assets/art/room1_revision_20261013/pod_closed_v3.glb")
const OLD_OPEN := preload("res://assets/art/room1_revision_20261013/pod_open_v3.glb")
const NEW_CLOSED := preload("res://assets/art/room1_pod_volume_v4/pod_closed_v4.glb")
const NEW_OPEN := preload("res://assets/art/room1_pod_volume_v4/pod_open_v4.glb")
const SURFACE := preload("res://scripts/dev/room1_pod_volume_surface_v4.gdshader")
const GLASS := preload("res://scripts/dev/room1_pod_volume_glass_v4.gdshader")
const OLD_GLASS := preload("res://scripts/dev/room1_glass_chamber_transmission_r2.gdshader")
var models: Dictionary={}
var glass_materials: Array[ShaderMaterial]=[]
var glass_meshes: Array[MeshInstance3D]=[]
var camera: Camera3D
var chamber: OmniLight3D
var info: Label
var revised := true
var opened := true
var glass_visible := true
var chamber_powered := true
var reflections_on := true
var view_index := 0

func _ready() -> void:
	var world:=WorldEnvironment.new();var environment:=Environment.new();world.environment=environment
	environment.background_mode=Environment.BG_COLOR;environment.background_color=Color("263039")
	environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;environment.ambient_light_color=Color("AAB9C2");environment.ambient_light_energy=.20
	add_child(world)
	var key:=DirectionalLight3D.new();key.rotation_degrees=Vector3(-48,-35,0);key.light_color=Color("E3E9E8");key.light_energy=.75;key.shadow_enabled=true;add_child(key)
	var fill:=DirectionalLight3D.new();fill.rotation_degrees=Vector3(-22,140,0);fill.light_color=Color("96B1C0");fill.light_energy=.10;add_child(fill)
	var floor:=MeshInstance3D.new();var floor_mesh:=BoxMesh.new();floor_mesh.size=Vector3(5.0,.10,5.0);floor.mesh=floor_mesh;floor.position.y=-.07
	var mat:=StandardMaterial3D.new();mat.albedo_color=Color("5A6C73");mat.roughness=1.0;floor.material_override=mat;add_child(floor)
	chamber=OmniLight3D.new();chamber.position=Vector3(0,.39,-.64);chamber.light_color=Color("C1D9DE");chamber.light_energy=.055;chamber.omni_range=1.45;chamber.omni_attenuation=1.4;chamber.shadow_enabled=true;add_child(chamber)
	for item in [{"key":"old_closed","scene":OLD_CLOSED,"new":false},{"key":"old_open","scene":OLD_OPEN,"new":false},{"key":"new_closed","scene":NEW_CLOSED,"new":true},{"key":"new_open","scene":NEW_OPEN,"new":true}]:
		var model:Node3D=item.scene.instantiate();add_child(model);models[item.key]=model;_materials(model,item.new)
	camera=Camera3D.new();camera.current=true;camera.near=.03;camera.far=100;add_child(camera)
	var layer:=CanvasLayer.new();add_child(layer);info=Label.new();info.position=Vector2(18,16);info.add_theme_font_size_override("font_size",17);layer.add_child(info)
	set_state(true,true);set_view(0)

func _materials(model: Node3D,new_version: bool) -> void:
	for mesh:MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		for surface in mesh.mesh.get_surface_count():
			var original:=mesh.get_active_material(surface) as BaseMaterial3D
			if original==null:continue
			var name_text: String=mesh.name.to_lower()+" "+original.resource_name.to_lower()
			var is_glass:=name_text.contains("glass")
			var material:=ShaderMaterial.new()
			if is_glass:
				material.shader=GLASS if new_version else OLD_GLASS
				material.set_shader_parameter("glass_pixels" if new_version else "pixel_reflections",original.albedo_texture)
				if not new_version:material.set_shader_parameter("chamber_light_position",Vector3(0,.39,-.64))
				glass_materials.append(material);glass_meshes.append(mesh);mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			else:
				material.shader=SURFACE;material.set_shader_parameter("color_map",original.albedo_texture);material.set_shader_parameter("tint",original.albedo_color)
			mesh.set_surface_override_material(surface,material)

func set_state(new_version: bool,open_pose: bool) -> void:
	revised=new_version;opened=open_pose
	for key in models:models[key].visible=(key==("new_" if revised else "old_")+("open" if opened else "closed"))
	set_glass_visible(glass_visible);set_chamber_power(chamber_powered);_info()
func set_glass_visible(enabled: bool) -> void:
	glass_visible=enabled
	for mesh in glass_meshes:mesh.visible=enabled
	_info()
func set_chamber_power(enabled: bool) -> void:
	chamber_powered=enabled;chamber.visible=enabled
	for material in glass_materials:
		if material.shader==OLD_GLASS:material.set_shader_parameter("chamber_powered",1.0 if enabled else 0.0)
	_info()
func set_reflections(enabled: bool) -> void:
	reflections_on=enabled
	for material in glass_materials:
		if material.shader==GLASS:material.set_shader_parameter("reflections_enabled",1.0 if enabled else 0.0)
		else:material.set_shader_parameter("reflection_strength",1.0 if enabled else 0.0)
	_info()
func set_view(index: int) -> void:
	view_index=clampi(index,0,5)
	var views=[{"p":Vector3(-3.3,2.55,3.9),"t":Vector3(.12,.42,0),"f":38.0},{"p":Vector3(-3.2,1.0,1.0),"t":Vector3(.1,.48,0),"f":44.0},{"p":Vector3(-2.2,.75,2.5),"t":Vector3(.55,.67,-.12),"f":39.0},{"p":Vector3(-1.5,1.45,-2.1),"t":Vector3(0,.55,-.64),"f":37.0},{"p":Vector3(.2,1.25,4.6),"t":Vector3(.13,.47,0),"f":44.0},{"p":Vector3(-2.0,1.5,-2.6),"t":Vector3(.12,.52,-.1),"f":42.0}]
	var view:Dictionary=views[view_index];camera.position=view.p;camera.look_at(view.t);camera.fov=view.f;_info()
func _info() -> void:
	if info:info.text="单舱体积/透明/像素旧化 v4 · %s · %s\nV旧/新 O闭/开 1–6视角 G舱内光 T玻璃 R反光 H说明\n独立审图灯光；不是整室新烘焙或最终游戏光照。" % ["新v4" if revised else "原v3","开45°" if opened else "关闭"]
func _unhandled_key_input(event: InputEvent) -> void:
	if not(event is InputEventKey and event.pressed and not event.echo):return
	match event.physical_keycode:
		KEY_V:set_state(not revised,opened)
		KEY_O:set_state(revised,not opened)
		KEY_G:set_chamber_power(not chamber_powered)
		KEY_T:set_glass_visible(not glass_visible)
		KEY_R:set_reflections(not reflections_on)
		KEY_H:info.visible=not info.visible
	if event.physical_keycode>=KEY_1 and event.physical_keycode<=KEY_6:set_view(event.physical_keycode-KEY_1)
