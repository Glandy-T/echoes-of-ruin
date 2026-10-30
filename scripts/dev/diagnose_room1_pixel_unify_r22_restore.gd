extends Node

const OUT := "res://docs/art/experiments/room1_pixel_unify_r22/evidence/restore_diagnosis/"
var room: Node3D
var camera: Camera3D
var hero: Node3D
var records: Array[Dictionary] = []

func _ready() -> void:
	call_deferred("run")

func _look_p12() -> void:
	camera.global_position = Vector3(1.775, 1.8, -4.45)
	camera.look_at(Vector3(3.65, .43, -7.65), Vector3.UP)
	camera.fov = 44.0

func _state() -> Dictionary:
	var pod_material: ShaderMaterial = hero.get("_surface_materials")[0]
	var shell_material: ShaderMaterial = room.complete_shell_materials[0]
	return {
		"mode": room.r22_mode,
		"pose": str(hero.get_state_name()),
		"pod_pose_blend": pod_material.get_shader_parameter("pose_blend"),
		"room_pose_blend": shell_material.get_shader_parameter("room_pose_blend"),
		"closed_irradiance": (pod_material.get_shader_parameter("closed_irradiance") as Texture2D).resource_path,
		"open_irradiance": (pod_material.get_shader_parameter("open_irradiance") as Texture2D).resource_path,
		"strip_irradiance": (shell_material.get_shader_parameter("strip_irradiance") as Texture2D).resource_path,
		"strip_irradiance_open": (shell_material.get_shader_parameter("strip_irradiance_open") as Texture2D).resource_path,
	}

func _shot(name: String) -> void:
	room._sync_render_camera()
	room._sync_bloom_camera()
	room._sync_standard_visuals()
	room._sync_complete_room_pose()
	room._sync_complete_screen_sources()
	room._sync_door_glow()
	for _i in 12:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.save_png(OUT + name + ".png") == OK)
	records.append({"file": name + ".png", "state": _state()})
	print("R22_RESTORE_DIAG ", name, " ", JSON.stringify(_state()))

func _settle_view(position: Vector3, target: Vector3, fov: float) -> void:
	camera.global_position = position
	camera.look_at(target, Vector3.UP)
	camera.fov = fov
	room._sync_render_camera()
	room._sync_bloom_camera()
	for _i in 12:
		await get_tree().process_frame

func _camera_sweep(include_pods: bool) -> void:
	var views: Array = [
		[Vector3(10.5, 13, 6.5), Vector3(10.5, 0, -4.75), 78.0],
		[Vector3(2.5, 1.9, -6.2), Vector3(.2, 1.45, -9.25), 60.0],
		[Vector3(18.5, 1.9, -6.2), Vector3(20.8, 1.45, -9.25), 60.0],
		[Vector3(10.5, 2.55, -4.3), Vector3(10.5, 2.1, -9.25), 60.0],
		[Vector3(10.5, 10, 2.5), Vector3(10.5, .05, -4.75), 80.0],
	]
	for view: Array in views:
		await _settle_view(view[0], view[1], view[2])
	var front: MeshInstance3D = room.get_node("Shell").find_child("Wall_front", true, false)
	var old_visible := front.visible
	var old_shadow := front.cast_shadow
	front.visible = true
	front.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for view: Array in [
		[Vector3(2.5, 1.9, -3.2), Vector3(.2, 1.45, -.25), 70.0],
		[Vector3(18.5, 1.9, -3.2), Vector3(20.8, 1.45, -.25), 70.0],
		[Vector3(10.5, 2.0, -5.7), Vector3(10.5, 1.6, -.2), 70.0],
	]:
		await _settle_view(view[0], view[1], view[2])
	front.visible = old_visible
	front.cast_shadow = old_shadow
	if include_pods:
		for record: Dictionary in room.room_pod_records:
			var pod: Node3D = room.room_pods[str(record.id)]
			await _settle_view(pod.to_global(Vector3(-1.0, 1.4, 2.9)), pod.to_global(Vector3(0, .35, 0)), 48.0)

func run() -> void:
	room = get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for _i in 120:
		await get_tree().process_frame
	room.finish_exit()
	room.review_ui.close_dialogue()
	room.actor_shadow_on = false
	room._sync_actor_shadow()
	for _i in 120:
		await get_tree().process_frame
	for key in ["paper_hero", "bloom_paper_hero"]:
		var actor: Sprite3D = room.get(key)
		if actor:
			actor.visible = false
	room.info.get_parent().hide()
	var ui: Node = room.review_ui
	if ui.get("pause_button"):
		(ui.get("pause_button") as Control).hide()
	camera = room.get_node("ReviewCamera") as Camera3D
	hero = room.room_pods["P12"]
	room.set_process(false)
	room.set_physics_process(false)
	_look_p12()

	room.set_r22_mode(1)
	hero.set_open_immediate(false)
	await _shot("00_a_start")
	await _shot("01_a_repeat")

	room.set_r22_mode(2)
	await _shot("02_b_closed")
	room.set_r22_mode(1)
	await _shot("03_a_after_material_switch")

	hero.set_open_immediate(true)
	await _shot("04_a_open")
	hero.set_open_immediate(false)
	await _shot("05_a_after_open_close")

	room.set_r22_mode(2)
	hero.set_open_immediate(true)
	await _shot("06_b_open")
	hero.set_open_immediate(false)
	room.set_r22_mode(1)
	await _shot("07_a_after_b_open_close")
	await _shot("08_a_final_repeat")
	await _camera_sweep(false)
	_look_p12()
	await _shot("09_a_after_room_camera_sweep")
	await _camera_sweep(true)
	_look_p12()
	await _shot("10_a_after_pod_camera_sweep")

	FileAccess.open(OUT + "state_record.json", FileAccess.WRITE).store_string(JSON.stringify(records, "\t"))
	get_tree().quit()
