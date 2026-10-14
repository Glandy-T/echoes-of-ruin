extends SceneTree
const OUTPUT := "res://docs/art/experiments/room1_player_physics_test_r1/"
var room: Node
var checks := {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	room = (load("res://scenes/dev/room1_player_physics_test_r1.tscn") as PackedScene).instantiate()
	get_root().add_child(room)
	room.test_mode = true
	await process_frame
	assert(room.pod_bodies.size() == 20 and room.shell_bodies.size() == 9)
	assert(room.actual_strip_lights.is_empty())
	DirAccess.make_dir_recursive_absolute(OUTPUT)
	room.teleport_player(Vector3(10.5, 1.0, -4.75))
	await ticks(50)
	assert(room.player.is_on_floor() and absf(room.player.position.y) < 0.015)
	checks["gravity_and_floor"] = room.player.position.y
	await capture("01_center_shadow.png")
	room.actor_shadow_on = false
	room._sync_actor_shadow()
	await capture("02_center_no_shadow.png")
	room.actor_shadow_on = true
	room._sync_actor_shadow()
	room.teleport_player(Vector3(3.525, 0.05, -4.75))
	await ticks(20)
	var rear_contacts := await drive(Vector2(0, -1), 100)
	assert(rear_contacts.has("Solid_P12"))
	assert(room.player.position.z > -6.4 and room.player.position.z < -6.1)
	assert_no_pod_overlap()
	checks["rear_pod_block"] = {"position": room.player.position, "contacts": rear_contacts}
	await capture("03_rear_pod_block.png")
	room.teleport_player(Vector3(3.525, 0.05, -4.75))
	await ticks(20)
	var front_contacts := await drive(Vector2(0, 1), 100)
	assert(front_contacts.has("Solid_P02"))
	assert(room.player.position.z < -3.1 and room.player.position.z > -3.4)
	assert_no_pod_overlap()
	checks["front_pod_block"] = {"position": room.player.position, "contacts": front_contacts}
	await capture("04_front_pod_block.png")
	var slide_contacts := await drive(Vector2(1, 1), 25)
	assert(room.player.position.x > 3.85 and absf(room.player.position.y) < 0.02)
	assert_no_pod_overlap()
	checks["slide_along_pod"] = {"position": room.player.position, "contacts": slide_contacts}
	await capture("05_slide.png")
	room.teleport_player(Vector3(4.4, 0.05, -4.75))
	await ticks(20)
	var gap_contacts := await drive(Vector2(0, 1), 150)
	for name in gap_contacts:
		assert(not name.begins_with("Solid_P"))
	assert(room.player.position.z > -0.5 and room.player.position.z < -0.35)
	assert_no_pod_overlap()
	checks["gap_pass_and_front_wall"] = {"position": room.player.position, "contacts": gap_contacts}
	await capture("06_gap_to_front_wall.png")
	room.teleport_player(Vector3(0.6, 0.05, -4.75))
	await ticks(20)
	var wall_contacts := await drive(Vector2(-1, 0), 60)
	assert(wall_contacts.has("Solid_Wall_left"))
	assert(room.player.position.x > 0.4 and room.player.position.x < 0.5)
	checks["left_wall_block"] = room.player.position
	await capture("07_left_wall.png")
	room.teleport_player(Vector3(10.5, 0.05, -4.75))
	await ticks(20)
	var moved_contacts := await drive(Vector2(1, 0), 35)
	checks["free_walk"] = room.player.position
	await capture("08_moved_shadow.png")
	room.actor_shadow_on = false
	room._sync_actor_shadow()
	await capture("09_moved_no_shadow.png")
	var differences := {}
	assert(is_equal_approx(room.get_node("ReviewCamera").position.y, room.camera_height_m))
	assert(room.get_node("ReviewCamera").basis.is_equal_approx(room.locked_basis))
	checks["camera_height_and_rotation_locked"] = true
	if DisplayServer.get_name() != "headless":
		differences["center_actor_shadow"] = difference("01_center_shadow.png", "02_center_no_shadow.png")
		differences["moved_actor_shadow"] = difference("08_moved_shadow.png", "09_moved_no_shadow.png")
		assert(differences.center_actor_shadow > 0.00001 and differences.moved_actor_shadow > 0.00001)
	var file := FileAccess.open(OUTPUT + "validation.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"engine": Engine.get_version_info().string, "pod_colliders": 20, "shell_colliders": room.shell_bodies.size(), "character_height": 1.65, "character_radius": 0.22, "strip_point_or_spot_lights": 0, "physics_checks": checks, "shadow_readback": differences, "scope": "Capsule CharacterBody3D with gravity and convex pod collision. Analytical capsule shadow on continuous-strip baked light; equipment lights use native shadows. Placeholder only; local review."}, "\t"))
	file.close()
	print("ROOM1_PHYSICS_PASS: ", JSON.stringify(checks), " shadows ", JSON.stringify(differences))
	quit()

func ticks(count: int) -> void:
	for frame in count:
		await physics_frame
	await process_frame

func drive(direction: Vector2, count: int) -> Array[String]:
	room.test_input = direction
	var contacts: Array[String] = []
	for frame in count:
		await physics_frame
		for name: String in room.previous_contacts:
			if not contacts.has(name):
				contacts.append(name)
	room.test_input = Vector2.ZERO
	room.player.velocity = Vector3.ZERO
	await process_frame
	return contacts

func assert_no_pod_overlap() -> void:
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = room.player.get_child(0).shape
	query.transform = Transform3D(Basis.IDENTITY, room.player.global_position + Vector3(0, 0.825, 0))
	query.collision_mask = 1
	for hit in room.player.get_world_3d().direct_space_state.intersect_shape(query):
		assert(not str(hit.collider.name).begins_with("Solid_P"))

func capture(filename: String) -> void:
	for frame in 10:
		await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		assert(get_root().get_texture().get_image().save_png(OUTPUT + filename) == OK)

func difference(a: String, b: String) -> float:
	var first := Image.load_from_file(OUTPUT + a)
	var second := Image.load_from_file(OUTPUT + b)
	var total := 0.0
	var count := 0
	for y in range(140, first.get_height(), 2):
		for x in range(0, first.get_width(), 2):
			var delta := first.get_pixel(x, y) - second.get_pixel(x, y)
			total += (absf(delta.r) + absf(delta.g) + absf(delta.b)) / 3.0
			count += 1
	return total / count
