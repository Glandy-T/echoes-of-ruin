extends "res://scripts/dev/cryo_building_review_v1.gd"
## Approved C silhouette, complete two-flight assembly; isolated from production.

const FULL_ROOT := "res://assets/art/cryo_handrail_full_v1/"
const FULL_OUT := "res://docs/art/experiments/cryo_handrail_full_v1/evidence/"
const FULL_VIEWS := ["hero", "side", "upper", "landing", "grip", "wall_grip", "turn", "upper_end", "all", "wall_back", "lower_wall", "upper_wall"]
var gray_mode := false

func stair_state(t: float, dt: float, neutral := false) -> void:
	super.stair_state(t, dt, neutral)
	for bank in lights:
		for light: OmniLight3D in bank: light.light_energy *= .18

func _png(name: String) -> Texture2D:
	if name in ["C_BODY", "C_SLOT"]:
		var path := FULL_ROOT + "textures/" + name + ".png"
		if ResourceLoader.exists(path): return load(path) as Texture2D
		if FileAccess.file_exists(path): return ImageTexture.create_from_image(Image.load_from_file(ProjectSettings.globalize_path(path)))
		return null
	return super._png(name)

func mat(name: String, distant := false) -> StandardMaterial3D:
	if gray_mode:
		var key := "gray_" + name
		if material_cache.has(key): return material_cache[key]
		var m := StandardMaterial3D.new()
		m.albedo_color = Color("919794")
		m.roughness = .90
		m.metallic_specular = .12
		material_cache[key] = m
		return m
	var surface := super.mat(name, distant)
	if name == "C_SLOT": surface.albedo_color = Color("98a4a0")
	return surface

func show_variant(_id: String) -> void:
	reset_stage("HR-C-FULL")
	var model := (load(FULL_ROOT + "cryo_handrail_full_v1.glb") as PackedScene).instantiate() as Node3D
	stage.add_child(model)
	for mesh_node: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		for surface in mesh_node.mesh.get_surface_count():
			var source := mesh_node.get_active_material(surface)
			if source: mesh_node.set_surface_override_material(surface, mat(source.resource_name))
		mesh_node.create_trimesh_collision()
	setup_stair_lights(model)
	setup_actor()
	world.background_color = Color("343e42")
	motion_running = true
	stair_state(3.1, 2.)
	hud.text = "C  一体化护栏 / 完整双跑"
	notice.text = "↑↓ 视角  ·  空格 暂停演示  ·  G 灰模/像素  ·  L 灯光故障演示  ·  独立审图"
	set_view("hero")

func set_view(view: String) -> void:
	view_name = view
	# Technical cuts are display-only; no geometry or game-camera changes.
	for node in stage.find_children("*", "MeshInstance3D", true, false):
		node.visible = true
	if view in ["hero", "side", "grip", "turn", "upper_end", "all"]:
		for pattern: String in ["L01_ZONE_UPPER*", "L01_ZONE_FLOOR*", "L01_TURN_UPPER_RETURN*", "Wall_Upper_Run*", "Wall_Upper_Floor*", "Wall_Turn_UpperReturn*"]:
			for node in stage.find_children(pattern, "MeshInstance3D", true, false): node.visible = false
	if view in ["wall_grip", "lower_wall", "upper_wall"]:
		for node in stage.find_children("C_Guard*", "MeshInstance3D", true, false): node.visible = false
	if view == "all":
		for pattern: String in ["Wall_Lower*", "L01_ZONE_LOWER*", "Wall_Turn_LowerReturn*", "L01_ZONE_TURN*"]:
			for node in stage.find_children(pattern, "MeshInstance3D", true, false): node.visible = false
	var p := Vector3(-7.10, 5.90, -1.45)
	var target := Vector3(.45, 2.50, -1.0)
	var size := 7.65
	match view:
		"side":
			p = Vector3(-4.9, 2.25, -.7); target = Vector3(1.6, 1.65, -.58); size = 3.5
		"upper":
			p = Vector3(-4.6, 4.9, -2.3); target = Vector3(2.3, 2.70, -1.93); size = 4.5
		"landing":
			p = Vector3(1.3, 3.4, -1.3); target = Vector3(2.6, 2.15, -1.35); size = 2.9
		"grip":
			p = Vector3(-.05, 2.40, 1.50); target = Vector3(.10, 1.90, -.90); size = 1.35
		"wall_grip":
			p = Vector3(-.15, 2.65, -.12); target = Vector3(.50, 2.1, .97); size = 2.0
		"turn":
			p = Vector3(3.40, 3.80, .75); target = Vector3(1.55, 2.60, -.90); size = 1.90
		"upper_end":
			p = Vector3(-4.5, 5.4, -.5); target = Vector3(-2.5, 4.3, -1.10); size = 2.5
		"all":
			p = Vector3(-4.8, 11., 7.); target = Vector3(.1, 2.2, -1.0); size = 8.5
		"wall_back":
			p = Vector3(2.80, 3.25, -1.0); target = Vector3(3.48, 3.25, -1.0); size = 4.10
		"lower_wall":
			p = Vector3(0., 2.40, -1.0); target = Vector3(0., 2.40, .90); size = 5.8
		"upper_wall":
			p = Vector3(0., 4.25, -.5); target = Vector3(0., 4.25, -2.90); size = 5.8
	camera.size = size
	camera.position = p
	camera.look_at(target, Vector3.UP)

func _unhandled_key_input(event: InputEvent) -> void:
	if capture_running or not event is InputEventKey or not event.pressed or event.echo: return
	if event.keycode in [KEY_UP, KEY_DOWN]:
		set_view(FULL_VIEWS[posmod(FULL_VIEWS.find(view_name) + (1 if event.keycode == KEY_UP else -1), FULL_VIEWS.size())])
	elif event.keycode == KEY_SPACE: motion_running = not motion_running
	elif event.keycode == KEY_L: state_fault = not state_fault
	elif event.keycode == KEY_G:
		var old_view := view_name
		gray_mode = not gray_mode
		show_variant("")
		set_view(old_view)

func save_capture(filename: String, view: String, state: String) -> void:
	set_view(view)
	for frame in 3: await get_tree().process_frame
	RenderingServer.force_draw()
	var picture := get_viewport().get_texture().get_image()
	assert(picture.get_size() == VIEW)
	assert(picture.save_png(FULL_OUT + filename + ".png") == OK)
	var energies: Array[float] = []
	for bank in lights:
		for light: OmniLight3D in bank: energies.append(light.light_energy)
	var hidden: Array[String] = []
	for mesh: MeshInstance3D in stage.find_children("*", "MeshInstance3D", true, false):
		if not mesh.visible: hidden.append(str(mesh.name))
	shots.append({"file": filename + ".png", "view": view, "state": state, "gray": gray_mode,
		"resolution": [1280, 720], "camera": str(camera.global_transform), "ortho_m": camera.size,
		"keep_aspect": camera.keep_aspect,
		"ambient_energy": world.ambient_light_energy, "sun_energy": sun.light_energy,
		"point_energies": energies, "zone_factors": lit.duplicate(), "missing": missing.keys(),
		"baked_light": false, "filter": "nearest", "density_target": 80, "hidden_meshes": hidden})

func probe_clearance() -> void:
	await get_tree().physics_frame
	await get_tree().physics_frame
	var state := get_world_3d().direct_space_state
	var widths: Array[Dictionary] = []
	var poses: Array[Dictionary] = []
	var capsule := CapsuleShape3D.new()
	capsule.radius = .125
	capsule.height = 1.62
	for upper: bool in [false, true]:
		for i in 11:
			var x := -1.65 + (i + .5) * .30
			var floor_height := (11 - i if upper else i + 1) * (1.90 / 12.) + (1.90 if upper else 0.)
			var z := -2. if upper else 0.
			var origin := Vector3(x, floor_height + .45, z)
			var left := state.intersect_ray(PhysicsRayQueryParameters3D.create(origin, origin + Vector3(0, 0, 1.3)))
			var right := state.intersect_ray(PhysicsRayQueryParameters3D.create(origin, origin - Vector3(0, 0, 1.3)))
			assert(not left.is_empty() and not right.is_empty())
			var width: float = left.position.distance_to(right.position)
			widths.append({"run": "upper" if upper else "lower", "x": x, "height_above_tread": .45, "width_m": width})
			assert(width >= 1.799)
			var q := PhysicsShapeQueryParameters3D.new()
			q.shape = capsule
			q.transform = Transform3D(Basis.IDENTITY, Vector3(x, floor_height + .82, z))
			q.margin = 0.
			var hits := state.intersect_shape(q, 8)
			poses.append({"run": "upper" if upper else "lower", "x": x, "overlap_count": hits.size()})
			assert(hits.is_empty())
	var center := Vector3(2.55, 2.35, -1.)
	var inner := state.intersect_ray(PhysicsRayQueryParameters3D.create(center, center - Vector3(1.5,0,0)))
	var outer := state.intersect_ray(PhysicsRayQueryParameters3D.create(center, center + Vector3(1.5,0,0)))
	assert(not inner.is_empty() and not outer.is_empty())
	var turn_width: float = inner.position.distance_to(outer.position)
	assert(turn_width >= 1.799)
	FileAccess.open(FULL_OUT + "runtime_clearance.json", FileAccess.WRITE).store_string(JSON.stringify({
		"flight_ray_widths": widths, "turn_apex_width_m": turn_width,
		"capsule_radius_m": .125, "capsule_height_m": 1.62, "tread_center_static_poses": poses,
		"scope": "Godot imported triangle collision rays and static capsule poses. Not a movement-controller or stair-climbing acceptance test."
	}, "\t"))

func capture_all() -> void:
	capture_running = true
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(FULL_OUT))
	for gray: bool in [true, false]:
		gray_mode = gray
		show_variant("")
		motion_running = false
		stair_state(3.1, 2., true)
		for view: String in FULL_VIEWS:
			actor.visible = view in ["hero", "side", "upper", "landing"]
			await save_capture(("gray_" if gray else "pixel_") + view, view, "neutral_surface_review")
	gray_mode = false
	show_variant("")
	motion_running = false
	await probe_clearance()
	state_fault = true
	stair_state(3.1, 2.)
	await save_capture("pixel_baseline", "hero", "minimum_0.2_fault_demo")
	state_fault = false
	stair_state(3.1, 2.)
	await save_capture("pixel_occupied", "hero", "occupied_realtime_lighting")
	for frame in 112:
		stair_state(float(frame) * .25, .25)
		await save_capture("motion_%03d" % frame, "hero", "scripted_28s_motion_not_physics_navigation")
	FileAccess.open(FULL_OUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify(shots, "\t"))
	print("FULL_HANDRAIL_CAPTURE_COMPLETE ", shots.size())
	get_tree().quit()
