@tool
extends "res://scripts/dev/room1_pixel_motion_test_r2.gd"

const HERO := "P12"
const END_TIME := 6.5
var exit_active := false
var exit_time := 0.0
var hero_origin := Vector3.ZERO
var bloom_actor: MeshInstance3D
var exit_previous_pose := Transform3D.IDENTITY
var exit_current_pose := Transform3D.IDENTITY
var open_hero_bake_root: String = "res://assets/art/room1_open_hero_bake_r1"

func set_pixel_mode(_index: int) -> void:
	super.set_pixel_mode(0)

func _ready() -> void:
	baked_geometry_path = open_hero_bake_root + "/room1_baked_uv2_r3.glb"
	irradiance_path = open_hero_bake_root + "/strip_irradiance_denoised.exr"
	super._ready()
	if Engine.is_editor_hint():
		return
	hero_origin = $Pods/P12.global_position
	# The bake places opaque parts in their approved open pose; glass isn't a receiver.
	var open_pod := (load("res://assets/art/room1_revision_20261013/pod_open_v3.glb") as PackedScene).instantiate()
	$Pods/P12.find_child("pod_v3_glass", true, false).transform = open_pod.find_child("pod_v3_glass", true, false).transform
	open_pod.free()
	_replace_hero_collision()
	_rebuild_hero_bloom_occlusion()
	for id in ["P02", "P17"]:
		room_screen_shaders[id].shader = preload("res://scripts/dev/room1_dead_screen_core_r1.gdshader")
		room_bloom_materials[id].shader = preload("res://scripts/dev/room1_dead_screen_bloom_r1.gdshader")
		screen_proxies[id].light_color = Color(1.0, 0.075, 0.025)
	for material in baked_receivers:
		material.shader = preload("res://scripts/dev/room1_exit_shadow_receiver_r1.gdshader")
	apply_sample_state()
	start_exit()

func _replace_hero_collision() -> void:
	var solid := $Pods/P12/Solid_P12
	solid.collision_layer = 0
	solid.queue_free()
	# Hollow shell, mattress and opened lid have individual surfaces, not a closed hull.
	for mesh: MeshInstance3D in $Pods/P12.find_children("*", "MeshInstance3D", true, false):
		if str(mesh.name) in ["pod_v3_glass", "pod_v3_display"] or mesh.mesh == null:
			continue
		var body := StaticBody3D.new()
		body.name = "OpenP12_" + str(mesh.name)
		body.collision_layer = 1
		body.collision_mask = 2
		add_child(body)
		body.global_transform = mesh.global_transform
		var collision := CollisionShape3D.new()
		collision.shape = mesh.mesh.create_trimesh_shape()
		body.add_child(collision)

func _rebuild_hero_bloom_occlusion() -> void:
	var world := bloom_camera.get_parent()
	for object in world.get_children():
		if object is MeshInstance3D and object.global_position.distance_to(hero_origin) < 1.0 and object.material_override not in room_bloom_materials.values():
			object.visible = false
			object.queue_free()
	var black := StandardMaterial3D.new()
	black.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	black.albedo_color = Color.BLACK
	for mesh: MeshInstance3D in $Pods/P12.find_children("*", "MeshInstance3D", true, false):
		if str(mesh.name) in ["pod_v3_glass", "pod_v3_display"]:
			continue
		var clone := MeshInstance3D.new()
		clone.mesh = mesh.mesh
		clone.material_override = black
		world.add_child(clone)
		clone.global_transform = mesh.global_transform
	bloom_actor = MeshInstance3D.new()
	bloom_actor.mesh = actor_mesh.mesh
	bloom_actor.material_override = black
	world.add_child(bloom_actor)

func start_exit() -> void:
	exit_active = true
	exit_time = 0.0
	player.collision_layer = 0
	player.collision_mask = 0
	player.velocity = Vector3.ZERO
	actor_mesh.visible = true
	apply_exit_pose(0.0)
	_update_info()

func eased(t: float, a: float, b: float) -> float:
	var u := clampf((t - a) / (b - a), 0.0, 1.0)
	return u * u * (3.0 - 2.0 * u)

func apply_exit_pose(t: float) -> void:
	var sit := eased(t, 1.2, 2.8)
	var rise := eased(t, 2.8, 4.2)
	var step := eased(t, 4.2, 5.5)
	var descend := eased(t, 5.5, END_TIME)
	var center_y := lerpf(0.51, 1.02, sit) + 0.33 * rise - 0.525 * descend
	var center_x := -0.20 * sit - 0.675 * step
	player.global_position = hero_origin + Vector3(center_x, center_y - 0.825, 0)
	actor_mesh.position = Vector3(0, 0.825, 0)
	actor_mesh.rotation.x = lerpf(-PI / 2.0, -deg_to_rad(25), sit) * (1.0 - rise)
	exit_current_pose = actor_mesh.global_transform
	exit_previous_pose = exit_current_pose
	$FollowTarget.position = player.position
	update_follow_camera()
	_sync_actor_shadow()

func finish_exit() -> void:
	apply_exit_pose(END_TIME)
	exit_active = false
	player.collision_layer = 2
	player.collision_mask = 1
	player.velocity = Vector3.ZERO
	actor_mesh.rotation = Vector3.ZERO
	_reset_motion_history()
	_update_info()

func _physics_process(delta: float) -> void:
	if exit_active:
		var last_pose := exit_current_pose
		exit_time = minf(exit_time + delta, END_TIME)
		apply_exit_pose(exit_time)
		exit_previous_pose = last_pose
		if exit_time >= END_TIME:
			finish_exit()
	else:
		super._physics_process(delta)

func _process(delta: float) -> void:
	if exit_active:
		actor_mesh.global_transform = exit_previous_pose.interpolate_with(exit_current_pose, Engine.get_physics_interpolation_fraction())
		$FollowTarget.position = actor_mesh.global_position - Vector3(0, 0.825, 0)
		update_follow_camera()
		_sync_render_camera()
		_sync_bloom_camera()
		_layout_presentation()
	else:
		super._process(delta)
	_sync_actor_shadow()
	if bloom_actor:
		bloom_actor.global_transform = actor_mesh.global_transform
		bloom_actor.visible = actor_mesh.visible

func _sync_actor_shadow() -> void:
	super._sync_actor_shadow()
	if actor_mesh:
		for material in baked_receivers:
			material.set_shader_parameter("capsule_a", actor_mesh.global_transform * Vector3(0, -0.605, 0))
			material.set_shader_parameter("capsule_b", actor_mesh.global_transform * Vector3(0, 0.605, 0))

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.physical_keycode == KEY_R:
		start_exit()
	elif event.physical_keycode == KEY_SPACE and exit_active:
		finish_exit()
	elif not exit_active:
		super._unhandled_key_input(event)
	elif event.physical_keycode == KEY_H:
		info.get_parent().visible = not info.get_parent().visible

func _update_info() -> void:
	if info:
		info.text = "Room 1 / P12主角仓 · 出仓动作预演 r1\nR重播 · 空格跳过 · 出仓后WASD/方向键移动 · H说明\n共3亮仓：P12主角仓，P02/P17红屏（死亡）\n胶囊占位：苏醒→起身→跨出→落地；舱盖保持打开。"
