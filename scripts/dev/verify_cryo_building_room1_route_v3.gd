extends Node

# Headless physics readback for the independent Room 1 -> west stair review.
var errors: Array[String] = []


func _ready() -> void:
	call_deferred("_run")


func _run() -> void:
	var level := get_parent() as Node3D
	await get_tree().physics_frame
	await get_tree().physics_frame
	var player := level.get("player") as CharacterBody3D
	var colliders: Array = level.get("route_bodies")
	if not player or colliders.size() < 30:
		errors.append("Room 1 player or route collision geometry missing")
	if level.get_node_or_null("TemporaryExitBoundary"):
		errors.append("old artificial Room 1 exit blocker remains")
	var black := level.get_node_or_null("BlackDoorway") as MeshInstance3D
	if black and black.visible:
		errors.append("old black doorway remains visible")
	if level.get_node_or_null("OutsideRoute") == null:
		errors.append("outside route GLB missing")

	var rays := {}
	for spot in [
		["corridor_at_room_door", Vector3(10.5, 0.4, -10.8), Vector3(10.5, -0.5, -10.8)],
		["west_stair_approach", Vector3(-1.5, 0.4, -36.5), Vector3(-1.5, -0.5, -36.5)],
		["west_stair_4f_landing", Vector3(-1.5, 0.4, -38.9), Vector3(-1.5, -0.5, -38.9)],
		["west_stair_1f_landing", Vector3(-1.5, -11.0, -38.9), Vector3(-1.5, -12.0, -38.9)],
	]:
		var query := PhysicsRayQueryParameters3D.create(spot[1], spot[2], 1)
		var hit := level.get_world_3d().direct_space_state.intersect_ray(query)
		var hit_body := hit.get("collider") as CollisionObject3D
		rays[spot[0]] = str(hit_body.name) if hit_body else ""
		if hit.is_empty():
			errors.append("no collision surface under " + spot[0])

	# Use the inherited chip sensor and real sliding placeholder, then move the
	# existing CharacterBody through the doorway. This catches a leftover stop
	# collider or a gap between the Room 1 and corridor floor.
	level.call("finish_exit")
	level.call("teleport_player", Vector3(10.5, 0.05, -8.6))
	level.set("test_mode", true)
	level.set("test_input", Vector2.ZERO)
	for i in 310:
		await get_tree().physics_frame
	var door_open_fraction := float(level.get("door_fraction"))
	if door_open_fraction < 0.95:
		errors.append("chip sensor did not open Room 1 door")
	level.set("test_input", Vector2(0.0, -1.0))
	for i in 105:
		await get_tree().physics_frame
	var door_crossing := player.global_position
	level.set("test_input", Vector2.ZERO)
	if door_crossing.z > -10.0 or absf(door_crossing.y) > 0.3:
		errors.append("player could not walk from Room 1 into 4F corridor")
	# Continue on the actual frozen SW personnel route: west along the room
	# corridor, then north along the outer foyer to the open West-stair door.
	level.set("test_input", Vector2(0.0, 1.0))
	for i in 28:
		await get_tree().physics_frame
	level.set("test_input", Vector2(-1.0, 0.0))
	for i in 440:
		if player.global_position.x <= -1.0:
			break
		await get_tree().physics_frame
	var west_turn := player.global_position
	level.set("test_input", Vector2(0.0, -1.0))
	for i in 900:
		if player.global_position.z <= -36.5:
			break
		await get_tree().physics_frame
	var stair_approach := player.global_position
	level.set("test_input", Vector2.ZERO)
	if west_turn.x > -0.9 or stair_approach.z > -36.5 or absf(stair_approach.y) > 0.3:
		errors.append("player could not traverse authorized 4F corridor to West stair")
	# The south-side 4F stair door is the approved entry for SW. Cross its
	# landing, then follow the same two-flight U stair down three storeys.
	level.set("test_input", Vector2(0.0, -1.0))
	for i in 150:
		if player.global_position.z <= -39.9:
			break
		await get_tree().physics_frame
	var top_landing := player.global_position
	var descent_landings: Array[float] = []
	for storey in 3:
		level.set("test_input", Vector2(1.0, 0.0))
		for i in 200:
			if player.global_position.x >= 3.2:
				break
			await get_tree().physics_frame
		level.set("test_input", Vector2(0.0, 1.0))
		for i in 130:
			if player.global_position.z >= -37.9:
				break
			await get_tree().physics_frame
		level.set("test_input", Vector2(-1.0, 0.0))
		for i in 200:
			if player.global_position.x <= -1.5:
				break
			await get_tree().physics_frame
		descent_landings.append(player.global_position.y)
		if absf(player.global_position.y + (storey + 1) * 3.8) > 0.35:
			errors.append("west stair did not reach expected lower landing %d" % (storey + 1))
		if storey < 2:
			# At each lower floor, cross the entry landing to the other flight
			# before descending the next U-shaped run.
			level.set("test_input", Vector2(0.0, -1.0))
			for i in 130:
				if player.global_position.z <= -39.9:
					break
				await get_tree().physics_frame
	level.set("test_input", Vector2.ZERO)

	var start := Vector3(-0.78, 0.05, -37.9)
	level.call("teleport_player", start)
	level.set("test_mode", true)
	level.set("test_input", Vector2(1.0, 0.0))
	for i in 60:
		await get_tree().physics_frame
	var climbed := player.global_position
	level.set("test_input", Vector2.ZERO)
	if climbed.y < 0.35:
		errors.append("player failed to climb 4F west slope")

	level.call("teleport_player", Vector3(-0.78, 0.05, -39.9))
	level.set("test_input", Vector2(1.0, 0.0))
	for i in 60:
		await get_tree().physics_frame
	var descended := player.global_position
	level.set("test_input", Vector2.ZERO)
	if descended.y > -0.35:
		errors.append("player failed to descend 4F west slope")

	var report := {
		"schema": "cryo_building_room1_route_v3_physics_check",
		"result": "PASS" if errors.is_empty() else "FAIL",
		"errors": errors,
		"route_collision_bodies": colliders.size(),
		"room1_door_open_fraction": door_open_fraction,
		"room1_to_corridor_end": [door_crossing.x, door_crossing.y, door_crossing.z],
		"west_corridor_turn": [west_turn.x, west_turn.y, west_turn.z],
		"west_stair_approach": [stair_approach.x, stair_approach.y, stair_approach.z],
		"west_stair_top_landing": [top_landing.x, top_landing.y, top_landing.z],
		"west_stair_descent_landing_y": descent_landings,
		"rays": rays,
		"climb_end": [climbed.x, climbed.y, climbed.z],
		"descent_end": [descended.x, descended.y, descended.z],
		"1f_external_exit": "TBD"
	}
	print(JSON.stringify(report))
	var file := FileAccess.open("res://docs/art/experiments/cryo_building_room1_route_v3/physics_validation.json", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "\t"))
	get_tree().quit(0 if errors.is_empty() else 1)
