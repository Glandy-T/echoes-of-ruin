@tool
extends "res://scripts/dev/room1_lighting_continuous_bake_r3.gd"

var player: CharacterBody3D
var actor_mesh: MeshInstance3D
var actor_material: ShaderMaterial
var pod_bodies: Array[StaticBody3D] = []
var shell_bodies: Array[StaticBody3D] = []
var physics_ready := false
var actor_shadow_on := true
var test_input := Vector2.ZERO
var test_mode := false
var previous_contacts: Array[String] = []

func _ready() -> void:
	super._ready()
	movement_view = false
	$FollowTarget/ScaleMarker.visible = false
	_build_colliders()
	player = CharacterBody3D.new()
	player.name = "PlayerPrototype"
	player.collision_layer = 2
	player.collision_mask = 1
	player.floor_snap_length = 0.12
	player.safe_margin = 0.001
	player.floor_max_angle = deg_to_rad(35.0)
	add_child(player)
	var shape := CapsuleShape3D.new()
	shape.radius = 0.22
	shape.height = 1.65
	var collision := CollisionShape3D.new()
	collision.shape = shape
	collision.position.y = 0.825
	player.add_child(collision)
	actor_mesh = MeshInstance3D.new()
	actor_mesh.mesh = $FollowTarget/ScaleMarker.mesh
	actor_mesh.position.y = 0.825
	actor_mesh.layers = 1
	actor_material = ShaderMaterial.new()
	actor_material.shader = preload("res://scripts/dev/room1_actor_strip_lighting_r1.gdshader")
	actor_mesh.material_override = actor_material
	player.add_child(actor_mesh)
	for material in baked_receivers:
		material.shader = preload("res://scripts/dev/room1_player_shadow_receiver_r1.gdshader")
	physics_ready = true
	teleport_player(START + Vector3(0, 0.05, 0))
	_sync_actor_shadow()
	_update_info()

func _build_colliders() -> void:
	for mesh: MeshInstance3D in $Shell.find_children("*", "MeshInstance3D", true, false):
		if mesh.name.begins_with("@") or mesh.mesh == null:
			continue
		var body := StaticBody3D.new()
		body.name = "Solid_" + str(mesh.name)
		body.collision_layer = 1
		body.collision_mask = 2
		add_child(body)
		body.global_transform = mesh.global_transform
		var collision := CollisionShape3D.new()
		collision.shape = mesh.mesh.create_trimesh_shape()
		body.add_child(collision)
		shell_bodies.append(body)
	for pod: Node3D in $Pods.get_children():
		var points := PackedVector3Array()
		for mesh: MeshInstance3D in pod.find_children("*", "MeshInstance3D", true, false):
			if not str(mesh.name) in ["pod_v3_lid", "pod_v3_shell_side", "pod_v3_shell_end"]:
				continue
			for surface in mesh.mesh.get_surface_count():
				var vertices: PackedVector3Array = mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
				for vertex in vertices:
					points.append(pod.global_transform.affine_inverse() * (mesh.global_transform * vertex))
		var shape := ConvexPolygonShape3D.new()
		shape.points = points
		var collision := CollisionShape3D.new()
		collision.shape = shape
		var body := StaticBody3D.new()
		body.name = "Solid_" + str(pod.name)
		body.collision_layer = 1
		body.collision_mask = 2
		pod.add_child(body)
		body.add_child(collision)
		pod_bodies.append(body)

func _physics_process(delta: float) -> void:
	if Engine.is_editor_hint() or not physics_ready:
		return
	var direction := test_input if test_mode else Vector2(float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)), float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
	direction = direction.limit_length()
	var acceleration := 10.0 if direction.length_squared() > 0.0 else 14.0
	player.velocity.x = move_toward(player.velocity.x, direction.x * 2.0, acceleration * delta)
	player.velocity.z = move_toward(player.velocity.z, direction.y * 2.0, acceleration * delta)
	player.velocity.y = -0.1 if player.is_on_floor() else player.velocity.y - 9.8 * delta
	player.move_and_slide()
	previous_contacts.clear()
	for index in player.get_slide_collision_count():
		var object := player.get_slide_collision(index).get_collider() as Node
		if object:
			previous_contacts.append(str(object.name))
	$FollowTarget.position = player.position
	update_follow_camera()
	_sync_actor_shadow()
	_update_info()

func _process(_delta: float) -> void:
	if not Engine.is_editor_hint() and bloom_camera:
		_sync_bloom_camera()

func _sync_actor_shadow() -> void:
	if not physics_ready:
		return
	for material in baked_receivers:
		material.set_shader_parameter("actor_feet", player.global_position)
		material.set_shader_parameter("actor_shadow_enabled", 1.0 if actor_shadow_on and actor_mesh.visible else 0.0)
	actor_material.set_shader_parameter("strip_on", 1.0 if strip_on else 0.0)

func teleport_player(point: Vector3) -> void:
	player.global_position = point
	player.velocity = Vector3.ZERO
	$FollowTarget.position = point
	update_follow_camera()
	_sync_actor_shadow()

func _unhandled_key_input(event: InputEvent) -> void:
	if Engine.is_editor_hint() or not physics_ready or not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.physical_keycode >= KEY_1 and event.physical_keycode <= KEY_9:
		teleport_player(EDGE_POSITIONS[event.physical_keycode - KEY_1] + Vector3(0, 0.05, 0))
	match event.physical_keycode:
		KEY_R: teleport_player(START + Vector3(0, 0.05, 0))
		KEY_L: strip_on = not strip_on
		KEY_G: windows_on = not windows_on
		KEY_B: screens_on = not screens_on
		KEY_N: halo_on = not halo_on
		KEY_K: actor_shadow_on = not actor_shadow_on
		KEY_C: get_tree().debug_collisions_hint = not get_tree().debug_collisions_hint
		KEY_T: actor_mesh.visible = not actor_mesh.visible
		KEY_H: info.get_parent().visible = not info.get_parent().visible
	apply_sample_state()
	_sync_actor_shadow()
	_update_info()

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 人物阴影＋舱碰撞 r1 · 待审\nWASD/方向键移动 · R复位 · 1–9位置 · C碰撞显示\nK人物阴影 %s · L灯带 · G舱光 · B屏幕 · N光晕 · H说明\n胶囊占位体1.65m，连续灯带实时遮挡；20舱实体碰撞。" % actor_shadow_on
