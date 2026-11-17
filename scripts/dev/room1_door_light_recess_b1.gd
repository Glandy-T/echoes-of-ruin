extends "res://scripts/dev/room1_door_powder_r32.gd"

# Door light direction B (user, 2026-11-17: r18 reads too bright / the strip is
# too conspicuous).  The r32 door surface is fixed (mode 3).  Key 4/5 compare:
#   4 = current r17 core + r18 soft glow
#   5 = B: lamp core dimmed and desaturated like a slot seen at a grazing angle,
#       a weak r18 halo, and a soft wash on the reveal faces and threshold that
#       fades from the slot toward the room.
const WASH_SHADER := preload("res://scripts/dev/door_recess_wash_b1.gdshader")
const R18_PHOSPHOR := {"phosphor_color": Vector3(0.34, 0.82, 0.44), "phosphor_energy": 0.78}
const B_PHOSPHOR := {"phosphor_color": Vector3(0.36, 0.66, 0.46), "phosphor_energy": 0.45}
# User (2026-11-17): add a little halo back.  The r18 halo follows the core's
# energy, so at 0.45 core and 1.1 strength it is about 60% of r18's (0.6 was invisible).
const B_HALO_STRENGTH := 1.1

var light_mode := 5
var wash_faces: Array[MeshInstance3D] = []
var wash_materials: Array[ShaderMaterial] = []

func _replace_placeholder() -> void:
	super._replace_placeholder()
	_build_wash()

func _wash_face(name: String, kind: int, points: PackedVector3Array) -> void:
	var material := ShaderMaterial.new()
	material.shader = WASH_SHADER
	material.set_shader_parameter("face_kind", kind)
	var data: Array = []; data.resize(Mesh.ARRAY_MAX)
	data[Mesh.ARRAY_VERTEX] = points
	data[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	var mesh := ArrayMesh.new(); mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, data)
	var part := MeshInstance3D.new(); part.name = name; part.mesh = mesh
	part.material_override = material
	part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	integrated_root.add_child(part)
	wash_faces.append(part); wash_materials.append(material)

func _build_wash() -> void:
	# Opening in root-local space (root at the opening centre, 1.2 m up):
	# x +-0.70, y -1.2..+1.2, wall depth z -0.0775 (corridor side) .. +0.1225 (room face).
	# Overlay faces sit 2 mm inside the opening to avoid z-fighting.
	var zb := -0.0775; var zf := 0.1225; var yb := -1.198; var yt := 1.198; var x := 0.698
	_wash_face("RecessWash_Left", 0, PackedVector3Array([Vector3(-x, yb, zb), Vector3(-x, yb, zf), Vector3(-x, yt, zf), Vector3(-x, yt, zb)]))
	_wash_face("RecessWash_Right", 0, PackedVector3Array([Vector3(x, yb, zb), Vector3(x, yt, zb), Vector3(x, yt, zf), Vector3(x, yb, zf)]))
	_wash_face("RecessWash_Header", 1, PackedVector3Array([Vector3(-x, yt, zb), Vector3(-x, yt, zf), Vector3(x, yt, zf), Vector3(x, yt, zb)]))
	# Threshold continues 0.6 m into the room, fading fast.
	_wash_face("RecessWash_Threshold", 2, PackedVector3Array([Vector3(-x, yb, zb), Vector3(x, yb, zb), Vector3(x, yb, zf + 0.6), Vector3(-x, yb, zf + 0.6)]))

func set_light_mode(mode: int) -> void:
	light_mode = clampi(mode, 4, 5)
	var phosphor: Dictionary = B_PHOSPHOR if light_mode == 5 else R18_PHOSPHOR
	for key: String in phosphor:
		inner_light_material.set_shader_parameter(key, phosphor[key])
	set_door_glow(true)
	var composite := door_glow_overlay.material as ShaderMaterial
	composite.set_shader_parameter("strength", B_HALO_STRENGTH if light_mode == 5 else 1.0)
	_update_feedback()
	_update_info()

func _update_feedback() -> void:
	super._update_feedback()
	if wash_materials.is_empty() or not is_instance_valid(door_mesh):
		return
	var center: Vector3 = integrated_root.to_local(door_mesh.global_position)
	var box := door_mesh.get_aabb()
	var on := 1.0 if light_mode == 5 and feedback_state == "pass" and door_fraction > 0.005 else 0.0
	for m in wash_materials:
		m.set_shader_parameter("passage_power", on)
		m.set_shader_parameter("leaf_min_x", center.x + box.position.x - 0.010)
		m.set_shader_parameter("leaf_max_x", center.x + box.end.x + 0.010)

func _capture_r30_baseline() -> void:
	super._capture_r30_baseline()
	set_light_mode(light_mode)

func _update_info() -> void:
	super._update_info()
	if info and is_instance_valid(inner_light_material):
		info.text += "\n门灯：" + ("4 现状 r17灯芯＋r18柔光" if light_mode == 4 else "5 方案B 灯芯藏槽＋弱光晕＋门洞内侧泛光") + "（4／5切换）"

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_4, KEY_5]:
		set_light_mode(4 if event.physical_keycode == KEY_4 else 5)
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)
