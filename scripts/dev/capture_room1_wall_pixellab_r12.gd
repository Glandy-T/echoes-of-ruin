extends Node
const OUT := "res://docs/art/experiments/room1_wall_pixellab_r12/evidence/"
var room: Node3D
var camera: Camera3D

func _ready() -> void:
	call_deferred("capture")

func snap(name: String) -> void:
	for i in 12: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var im := get_viewport().get_texture().get_image()
	assert(im.save_png(OUT + name + ".png") == OK)
	print("WALL_R12_SHOT ", name)

func technical() -> void:
	camera.global_position = Vector3(5.0, 2.5, -0.5)
	camera.look_at(Vector3(0.2, 1.6, -3.4))
	camera.fov = 58
	room.call("_sync_render_camera")
	room.call("_sync_bloom_camera")

func capture() -> void:
	room = get_parent() as Node3D
	DirAccess.make_dir_recursive_absolute(OUT)
	for i in 15: await get_tree().process_frame
	room.call("position_structure_review")
	for wall_name in room.get("full_materials"):
		if wall_name == "Floor_continuous_no_tile_seams": continue
		for material: ShaderMaterial in room.get("full_materials")[wall_name]:
			for side in ["left", "right", "front", "rear"]:
				var map := material.get_shader_parameter("full_wall_" + side + "_map") as Texture2D
				assert(map.resource_path == "res://assets/art/room1_wall_pixellab_r12/wall_" + side + ".png")
	room.set_process(false); room.set_physics_process(false)
	(room.get("info") as Label).get_parent().hide()
	for key in ["paper_hero", "bloom_paper_hero"]:
		var hero := room.get(key) as Sprite3D
		if hero: hero.hide()
	var ui := room.get("review_ui") as Node
	if ui and ui.get("pause_button"): (ui.get("pause_button") as Control).hide()
	camera = room.get_node("ReviewCamera") as Camera3D
	for enabled in [false, true]:
		room.call("set_wall_rework", enabled)
		var suffix := "after" if enabled else "before"
		room.call("teleport_player", Vector3(3.525, 0, -4.75))
		camera.fov = 50
		room.call("_sync_render_camera"); room.call("_sync_bloom_camera")
		await snap("game_left_" + suffix)
		for station in [["center",10.5],["right",17.475]]:
			room.call("teleport_player", Vector3(station[1],0,-4.75))
			room.call("_sync_render_camera"); room.call("_sync_bloom_camera")
			await snap("game_"+str(station[0])+"_"+suffix)
		technical()
		await snap("technical_" + suffix)
		room.call("set_base_color_mode", true)
		await snap("base_color_" + suffix)
		room.call("set_base_color_mode", false)
	# Confirm state restoration and inspect the complete room at unchanged light.
	room.call("set_wall_rework", true)
	technical(); await snap("technical_restored")
	var front := room.get_node("Shell").find_child("Wall_front", true, false) as MeshInstance3D
	front.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	var views := [
		["front_left", Vector3(3.0,2.1,-3.0), Vector3(0.25,1.5,-0.25)],
		["rear_left", Vector3(3.0,2.1,-6.2), Vector3(0.25,1.5,-9.25)],
		["front_right", Vector3(18.0,2.1,-3.0), Vector3(20.75,1.5,-0.25)],
		["rear_right", Vector3(18.0,2.1,-6.2), Vector3(20.75,1.5,-9.25)]]
	for view in views:
		camera.global_position = view[1]; camera.look_at(view[2]); camera.fov = 58
		room.call("_sync_render_camera"); room.call("_sync_bloom_camera")
		await snap("survey_" + str(view[0]))
	camera.global_position = Vector3(10.5,2.1,-6.0); camera.look_at(Vector3(10.5,1.6,-0.2)); camera.fov=90
	room.call("_sync_render_camera"); room.call("_sync_bloom_camera")
	await snap("survey_front_full")
	front.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	get_tree().quit()
