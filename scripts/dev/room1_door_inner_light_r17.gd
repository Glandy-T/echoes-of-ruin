extends "res://scripts/dev/room1_pod_pixellab_r16.gd"

const INNER_PHOSPHOR := preload("res://scripts/dev/door_inner_phosphor_r17.gdshader")
var inner_light_fixed:=true
var inner_light_material:ShaderMaterial
var inner_lights:Array[MeshInstance3D]=[]

func _replace_placeholder() -> void:
	super._replace_placeholder()
	_build_inner_light_faces()

func _face(name: String,points: PackedVector3Array) -> void:
	var normal:Vector3=(points[1]-points[0]).cross(points[2]-points[0]).normalized()
	var data:Array=[];data.resize(Mesh.ARRAY_MAX)
	data[Mesh.ARRAY_VERTEX]=points
	data[Mesh.ARRAY_NORMAL]=PackedVector3Array([normal,normal,normal,normal])
	data[Mesh.ARRAY_TEX_UV]=PackedVector2Array([Vector2(0,0),Vector2(1,0),Vector2(1,1),Vector2(0,1)])
	# Godot treats clockwise faces as front-facing; normals point into the room.
	data[Mesh.ARRAY_INDEX]=PackedInt32Array([0,2,1,0,3,2])
	var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,data)
	var part:=MeshInstance3D.new();part.name=name;part.mesh=mesh
	part.material_override=inner_light_material
	part.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	integrated_root.add_child(part);inner_lights.append(part)

func _build_inner_light_faces() -> void:
	inner_light_material=ShaderMaterial.new();inner_light_material.shader=INNER_PHOSPHOR
	# Only exposed room-facing bevels emit. The old front trim stays neutral.
	# Rear of the 85mm leaf is z=-0.0425; all new faces sit behind that plane,
	# but before the existing black doorway backdrop at z=-0.09.
	var bottom:float=0.005-integrated_root.global_position.y
	var obl:=Vector3(-0.695,bottom,-0.045);var obr:=Vector3(0.695,bottom,-0.045)
	var otl:=Vector3(-0.695,1.155,-0.045);var otr:=Vector3(0.695,1.155,-0.045)
	var ibl:=Vector3(-0.669,bottom,-0.075);var ibr:=Vector3(0.669,bottom,-0.075)
	var itl:=Vector3(-0.669,1.129,-0.075);var itr:=Vector3(0.669,1.129,-0.075)
	_face("InnerPhosphor_Left",PackedVector3Array([obl,ibl,itl,otl]))
	_face("InnerPhosphor_Right",PackedVector3Array([ibr,obr,otr,itr]))
	_face("InnerPhosphor_Header",PackedVector3Array([otl,itl,itr,otr]))
	_face("InnerPhosphor_Floor",PackedVector3Array([ibl,obl,obr,ibr]))

func set_inner_light_fix(enabled: bool) -> void:
	inner_light_fixed=enabled
	_update_feedback();_update_info()

func _update_feedback() -> void:
	super._update_feedback()
	if not is_instance_valid(inner_light_material) or not is_instance_valid(neutral_reveal):return
	for part in inner_lights:part.visible=inner_light_fixed
	if not inner_light_fixed:return
	for part:MeshInstance3D in integrated_root.find_children("JambLight_*","MeshInstance3D",true,false):
		part.material_override=neutral_reveal
		part.visible=part.name!=&"JambLight_Bottom"
	var center:Vector3=integrated_root.to_local(door_mesh.global_position)
	var box:=door_mesh.get_aabb()
	inner_light_material.set_shader_parameter("leaf_min_x",center.x+box.position.x-0.010)
	inner_light_material.set_shader_parameter("leaf_max_x",center.x+box.end.x+0.010)
	inner_light_material.set_shader_parameter("passage_power",1.0 if feedback_state=="pass" and door_fraction>0.005 else 0.0)

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode==KEY_F4:
		set_inner_light_fix(not inner_light_fixed);get_viewport().set_input_as_handled();return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		info.text="Room 1 / 门内侧荧光灯面 r17\nF4比较："+("仅露出的内侧灯面" if inner_light_fixed else "旧整圈门框变绿")+"\n靠近自动认证与开门；普通收边不发光，状态小窗保持。"
