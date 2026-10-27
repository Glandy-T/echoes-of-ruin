class_name CryopodStandardV8
extends Node3D

## Reusable Room 1 cryopod controller.  This deliberately owns only its GLB
## instance and never reaches into a room scene, so several pods remain isolated.

signal started(opening: bool)
signal finished(opened: bool)
signal state_changed(next_state: StringName)
signal screen_changed(texture: Texture2D)

enum MotionState { CLOSED, OPENING, OPEN, CLOSING }

const SURFACE_SHADER := preload("res://scripts/props/cryopod_standard_v8_surface.gdshader")
const TUBE_SHADER := preload("res://scripts/props/cryopod_standard_v8_tube.gdshader")
const GLASS_SHADER := preload("res://scripts/props/cryopod_standard_v8_glass.gdshader")
const SCREEN_SHADER := preload("res://scripts/props/cryopod_standard_v8_1_screen.gdshader")
const SCREEN_FONT := preload("res://assets/fonts/DotGothic16-Regular.ttf")

@export var closed_irradiance: Texture2D
@export var open_irradiance: Texture2D
@export_range(0.0, 3.0, 0.01) var baked_energy := 1.2
@export var tube_powered := true
@export var screen_powered := true
@export var glass_visible := true
@export var screen_name := "----"
@export var screen_status := "----"
@export var screen_background_tint := Color("526c76")
@export_range(0.0,1.0,0.01) var screen_background_energy := 0.8
@export_range(0.0, 1.0, 0.01) var screen_progress := 0.0
@export_range(0.0, 1.0, 0.01) var screen_secondary_progress := 0.0
@export_range(0.0, 1.0, 0.01) var screen_tertiary_progress := 0.0
@export var play_on_ready := false
@export var closing_blocker_check := true
@export_flags_3d_physics var closing_blocker_mask := 2

var motion_state: MotionState = MotionState.CLOSED
var _target_open := false
var _animation: AnimationPlayer
var _lid_motion: Node3D
var _display_mesh: MeshInstance3D
var _surface_materials: Array[ShaderMaterial] = []
var _tube_materials: Array[ShaderMaterial] = []
var _glass_materials: Array[ShaderMaterial] = []
var _screen_materials: Array[ShaderMaterial] = []
var _fixed_body: StaticBody3D
var _lid_body: AnimatableBody3D
var _mattress_body: StaticBody3D
var _screen_viewport: SubViewport
var _screen_name_label: Label
var _screen_status_label: Label

@onready var model: Node3D = $Model

func _ready() -> void:
	_resolve_contract_nodes()
	_make_instance_materials()
	_make_screen_overlay()
	_build_colliders()
	_apply_runtime_parameters()
	if _animation:
		_animation.animation_finished.connect(_on_animation_finished)
	set_open_immediate(play_on_ready)

func _process(_delta: float) -> void:
	_sync_lid_collision()
	# Prevent a closing animated lid from clipping a CharacterBody already in the
	# opening.  This is a narrow collision reliability guard, not a door system.
	if motion_state == MotionState.CLOSING and closing_blocker_check and _has_closing_blocker():
		_target_open = true
		motion_state = MotionState.OPENING
		state_changed.emit(get_state_name())
		started.emit(true)
		if _animation:
			_animation.play(&"LidOpen")
		return
	if not _animation:
		return
	var position := _animation.current_animation_position
	var length := _animation.current_animation_length
	if motion_state == MotionState.CLOSING and position <= 0.0005:
		_finish(false)
	elif motion_state == MotionState.OPENING and length > 0.0 and position >= length - 0.0005:
		_finish(true)
	_apply_pose_blend(length)

func get_model_root() -> Node3D:
	return model

func get_display_mesh() -> MeshInstance3D:
	return _display_mesh

func get_screen_texture() -> Texture2D:
	if not _screen_materials.is_empty():
		return _screen_materials[0].get_shader_parameter("screen_pixels") as Texture2D
	return null

func get_screen_overlay_texture() -> Texture2D:
	return _screen_viewport.get_texture() if _screen_viewport else null

func get_state_name() -> StringName:
	match motion_state:
		MotionState.CLOSED: return &"closed"
		MotionState.OPENING: return &"opening"
		MotionState.OPEN: return &"open"
		_: return &"closing"

func request_open() -> void:
	_request_pose(true)

func request_close() -> void:
	_request_pose(false)

func toggle() -> void:
	_request_pose(not _target_open)

func set_open_immediate(opened: bool) -> void:
	_target_open = opened
	if _animation:
		if not _animation.has_animation(&"LidOpen"):
			push_error("CryopodStandardV8 needs imported GLB animation LidOpen.")
			return
		_animation.play(&"LidOpen")
		_animation.pause()
		_animation.seek(_animation.get_animation(&"LidOpen").length if opened else 0.0, true)
	motion_state = MotionState.OPEN if opened else MotionState.CLOSED
	state_changed.emit(get_state_name())
	_sync_lid_collision()
	_apply_pose_blend(_animation.current_animation_length if _animation else 1.0)

func set_open_progress(progress: float) -> void:
	if not _animation or not _animation.has_animation(&"LidOpen"):
		push_error("CryopodStandardV8 cannot seek before LidOpen is imported from the GLB.")
		return
	_animation.play(&"LidOpen")
	_animation.pause()
	_animation.seek(clamp(progress, 0.0, 1.0) * _animation.get_animation(&"LidOpen").length, true)
	_target_open = progress >= 0.5
	motion_state = MotionState.OPEN if is_equal_approx(progress, 1.0) else MotionState.CLOSED if is_zero_approx(progress) else MotionState.OPENING if _target_open else MotionState.CLOSING
	state_changed.emit(get_state_name())
	_sync_lid_collision()
	_apply_pose_blend(_animation.current_animation_length)

func set_tube_powered(enabled: bool) -> void:
	tube_powered = enabled
	_apply_runtime_parameters()

func set_screen_powered(enabled: bool) -> void:
	screen_powered = enabled
	_apply_runtime_parameters()
	screen_changed.emit(get_screen_texture())

func set_screen_background(tint: Color, energy: float) -> void:
	screen_background_tint = tint
	screen_background_energy = clamp(energy,0.0,1.0)
	_apply_runtime_parameters()

func set_glass_visible(enabled: bool) -> void:
	glass_visible = enabled
	_apply_runtime_parameters()

func set_screen_state(next_name: String, next_status: String, next_progress: float, secondary_progress := -1.0, tertiary_progress := -1.0) -> void:
	screen_name = next_name
	screen_status = next_status
	screen_progress = clamp(next_progress, 0.0, 1.0)
	if secondary_progress >= 0.0: screen_secondary_progress = clamp(secondary_progress, 0.0, 1.0)
	if tertiary_progress >= 0.0: screen_tertiary_progress = clamp(tertiary_progress, 0.0, 1.0)
	_refresh_screen_overlay()
	_apply_runtime_parameters()
	screen_changed.emit(get_screen_texture())

func set_baked_energy(next_energy: float) -> void:
	baked_energy = maxf(next_energy, 0.0)
	_apply_runtime_parameters()

func set_pose_lightmaps(closed_map: Texture2D, open_map: Texture2D, energy := 1.2) -> void:
	closed_irradiance = closed_map
	open_irradiance = open_map
	baked_energy = maxf(energy, 0.0)
	_apply_runtime_parameters()

func set_actor_shadow_parameters(feet: Vector3, capsule_a: Vector3, capsule_b: Vector3, enabled: bool) -> void:
	for material in _surface_materials:
		material.set_shader_parameter("actor_feet", feet)
		material.set_shader_parameter("capsule_a", capsule_a)
		material.set_shader_parameter("capsule_b", capsule_b)
		material.set_shader_parameter("actor_shadow_enabled", 1.0 if enabled else 0.0)

func _request_pose(opened: bool) -> void:
	if not _animation or not _animation.has_animation(&"LidOpen"):
		push_error("CryopodStandardV8 needs an imported LidOpen GLB animation before it can move.")
		return
	if _target_open == opened and ((opened and motion_state == MotionState.OPEN) or (not opened and motion_state == MotionState.CLOSED)):
		return
	if not opened and closing_blocker_check and _has_closing_blocker():
		return
	_target_open = opened
	motion_state = MotionState.OPENING if opened else MotionState.CLOSING
	state_changed.emit(get_state_name())
	started.emit(opened)
	if opened:
		_animation.play(&"LidOpen")
	else:
		_animation.play_backwards(&"LidOpen")

func _finish(opened: bool) -> void:
	if (opened and motion_state != MotionState.OPENING) or (not opened and motion_state != MotionState.CLOSING):
		return
	_animation.pause()
	motion_state = MotionState.OPEN if opened else MotionState.CLOSED
	state_changed.emit(get_state_name())
	finished.emit(opened)
	_apply_pose_blend(_animation.current_animation_length)

func _on_animation_finished(animation_name: StringName) -> void:
	if animation_name == &"LidOpen" and motion_state == MotionState.OPENING:
		_finish(true)

func _apply_pose_blend(length: float) -> void:
	var blend := 1.0 if motion_state == MotionState.OPEN else 0.0
	if _animation and length > 0.0 and (motion_state == MotionState.OPENING or motion_state == MotionState.CLOSING):
		blend = clamp(_animation.current_animation_position / length, 0.0, 1.0)
	for material in _surface_materials:
		material.set_shader_parameter("pose_blend", blend)

func _resolve_contract_nodes() -> void:
	_lid_motion = _find_node_named(model, &"LidMotion") as Node3D
	_display_mesh = _find_node_named(model, &"PodDisplay") as MeshInstance3D
	_animation = _find_first_animation_player(model)
	if not _lid_motion:
		push_error("CryopodStandardV8 GLB contract is missing LidMotion.")
	if not _display_mesh:
		push_error("CryopodStandardV8 GLB contract is missing PodDisplay.")
	if not _animation:
		push_error("CryopodStandardV8 GLB contract is missing AnimationPlayer.")

func _make_instance_materials() -> void:
	for mesh: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		for surface in mesh.mesh.get_surface_count():
			var source := mesh.get_active_material(surface)
			var pixels := _albedo_texture(source)
			var material_key := _material_key(mesh, source)
			var material := ShaderMaterial.new()
			if mesh.name.begins_with("PodTubeDiffuser") or material_key.contains("pod_v8_tube_diffuser"):
				material.shader = TUBE_SHADER
				_tube_materials.append(material)
			elif mesh.name == &"PodGlass" or material_key.contains("pod_v8_glass"):
				material.shader = GLASS_SHADER
				material.set_shader_parameter("glass_pixels", pixels)
				_glass_materials.append(material)
			elif mesh.name == &"PodDisplay" or material_key.contains("pod_v8_display"):
				material.shader = SCREEN_SHADER
				material.set_shader_parameter("screen_pixels", pixels)
				_screen_materials.append(material)
				_display_mesh = mesh
			else:
				material.shader = SURFACE_SHADER
				material.set_shader_parameter("color_map", pixels)
				material.set_shader_parameter("base_color", _albedo_color(source))
				material.set_shader_parameter("receive_tubes", 1.0 if _receives_side_tubes(mesh, material_key) else 0.0)
				_surface_materials.append(material)
			mesh.set_surface_override_material(surface, material)

func _apply_runtime_parameters() -> void:
	for material in _surface_materials:
		material.set_shader_parameter("closed_irradiance", closed_irradiance)
		material.set_shader_parameter("open_irradiance", open_irradiance)
		material.set_shader_parameter("baked_energy", baked_energy)
		material.set_shader_parameter("has_baked_maps", 1.0 if closed_irradiance and open_irradiance else 0.0)
		material.set_shader_parameter("tube_powered", 1.0 if tube_powered else 0.0)
		material.set_shader_parameter("chamber_from_world", global_transform.affine_inverse())
	for material in _tube_materials:
		material.set_shader_parameter("tube_powered", 1.0 if tube_powered else 0.0)
	for material in _glass_materials:
		material.set_shader_parameter("glass_visible", 1.0 if glass_visible else 0.0)
	for material in _screen_materials:
		material.set_shader_parameter("powered", 1.0 if screen_powered else 0.0)
		material.set_shader_parameter("panel_tint", screen_background_tint)
		material.set_shader_parameter("panel_backlight", screen_background_energy)
		material.set_shader_parameter("progress", screen_progress)
		material.set_shader_parameter("secondary_progress", screen_secondary_progress)
		material.set_shader_parameter("tertiary_progress", screen_tertiary_progress)
		material.set_shader_parameter("screen_overlay", _screen_viewport.get_texture() if _screen_viewport else null)

func _make_screen_overlay() -> void:
	if _screen_materials.is_empty():
		return
	_screen_viewport = SubViewport.new()
	_screen_viewport.size = Vector2i(128, 48)
	_screen_viewport.transparent_bg = true
	_screen_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_screen_viewport)
	var layer := CanvasLayer.new()
	_screen_viewport.add_child(layer)
	var pixel_font := SCREEN_FONT.duplicate(true) as FontFile
	pixel_font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	pixel_font.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	_screen_name_label = _make_screen_label(pixel_font, Vector2(8, 7))
	_screen_status_label = _make_screen_label(pixel_font, Vector2(8, 20))
	layer.add_child(_screen_name_label)
	layer.add_child(_screen_status_label)
	_refresh_screen_overlay()

func _make_screen_label(font: FontFile, at: Vector2) -> Label:
	var label := Label.new()
	label.position = at
	label.size = Vector2(112, 11)
	label.add_theme_font_override("font", font)
	label.add_theme_font_size_override("font_size", 8)
	label.add_theme_color_override("font_color", Color("9ad7de"))
	label.clip_text = true
	return label

func _refresh_screen_overlay() -> void:
	if _screen_name_label:
		_screen_name_label.text = "NAME: " + screen_name
	if _screen_status_label:
		_screen_status_label.text = "SYS: " + screen_status

func _build_colliders() -> void:
	_fixed_body = $FixedShellCollision
	_lid_body = $LidCollision
	_mattress_body = $MattressCollision
	_sync_lid_collision()
	for mesh: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		if not mesh.mesh:
			continue
		var name_key := mesh.name.to_lower()
		if "podmattress" in name_key:
			_add_mesh_collision(_mattress_body, mesh)
		elif _lid_motion and _is_under(mesh, _lid_motion):
			_add_mesh_collision(_lid_body, mesh)
		elif name_key.contains("podshell") or name_key.contains("podinterior") or name_key.contains("podbasinseal") or name_key.contains("podtubehousing") or name_key.contains("poddisplayhousing"):
			_add_mesh_collision(_fixed_body, mesh)

func _sync_lid_collision() -> void:
	if _lid_body and _lid_motion:
		_lid_body.global_transform = _lid_motion.global_transform

func _add_mesh_collision(body: CollisionObject3D, mesh_instance: MeshInstance3D) -> void:
	var shape := mesh_instance.mesh.create_trimesh_shape()
	if not shape:
		return
	var collision := CollisionShape3D.new()
	collision.shape = shape
	body.add_child(collision)
	collision.global_transform = mesh_instance.global_transform

func _has_closing_blocker() -> bool:
	if closing_blocker_mask == 0 or not is_inside_tree():
		return false
	var query := PhysicsShapeQueryParameters3D.new()
	var envelope := BoxShape3D.new()
	# Covers only the human-access cavity while the lid travels, not its whole AABB.
	envelope.size = Vector3(0.94, 0.72, 1.86)
	query.shape = envelope
	query.transform = global_transform * Transform3D(Basis.IDENTITY, Vector3(0.0, 0.28, 0.0))
	query.collision_mask = closing_blocker_mask
	query.collide_with_bodies = true
	query.collide_with_areas = false
	var hits := get_world_3d().direct_space_state.intersect_shape(query, 8)
	return not hits.is_empty()

func _find_node_named(from: Node, expected: StringName) -> Node:
	if from.name == expected:
		return from
	for child in from.get_children():
		var found := _find_node_named(child, expected)
		if found:
			return found
	return null

func _find_first_animation_player(from: Node) -> AnimationPlayer:
	if from is AnimationPlayer:
		return from as AnimationPlayer
	for child in from.get_children():
		var found := _find_first_animation_player(child)
		if found:
			return found
	return null

func _is_under(node: Node, possible_parent: Node) -> bool:
	var current: Node = node
	while current:
		if current == possible_parent:
			return true
		current = current.get_parent()
	return false

func _albedo_texture(material: Material) -> Texture2D:
	if material is BaseMaterial3D:
		return (material as BaseMaterial3D).albedo_texture
	if material is ShaderMaterial:
		var shader_material := material as ShaderMaterial
		return shader_material.get_shader_parameter("color_map") as Texture2D
	return null

func _albedo_color(material: Material) -> Color:
	if material is BaseMaterial3D:
		return (material as BaseMaterial3D).albedo_color
	return Color.WHITE

func _material_key(mesh: MeshInstance3D, material: Material) -> String:
	return (mesh.name + " " + (material.resource_name if material else "")).to_lower()

func _receives_side_tubes(mesh: MeshInstance3D, material_key: String) -> bool:
	return mesh.name == &"PodInterior" or mesh.name == &"PodMattress" or material_key.contains("pod_v8_interior") or material_key.contains("pod_v8_mattress")
