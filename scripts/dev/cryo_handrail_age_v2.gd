extends "res://scripts/dev/cryo_handrail_full_v1.gd"
## Position-based PixelLab ageing. Same model/camera/light for both columns.
const AGE_ROOT := "res://assets/art/cryo_handrail_age_v2/"
const AGE_OUT := "res://docs/art/experiments/cryo_handrail_age_v2/evidence/"
const AGE_VIEWS := ["all", "hero", "grip", "wall_grip", "tread_contact", "platform_contact", "turn", "upper_end", "side", "upper", "landing", "wall_back", "lower_wall", "upper_wall"]
var ageing_on := true
var texture_map: Dictionary = {}

func show_variant(_id: String) -> void:
	reset_stage("HR-C-AGE")
	if texture_map.is_empty():
		texture_map = JSON.parse_string(FileAccess.get_file_as_string(AGE_ROOT + "material_map.json"))
	var model := (load(AGE_ROOT + "cryo_handrail_age_v2.glb") as PackedScene).instantiate() as Node3D
	stage.add_child(model)
	for node: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		for surface in node.mesh.get_surface_count():
			var source := node.get_active_material(surface) as StandardMaterial3D
			if source:
				var material := source.duplicate() as StandardMaterial3D
				material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
				if texture_map.has(source.resource_name):
					var key := "composite" if ageing_on else "base"
					var texture := load(AGE_ROOT + texture_map[source.resource_name][key]) as Texture2D
					assert(texture != null, "Missing comparison map: " + source.resource_name)
					material.albedo_texture = texture
				node.set_surface_override_material(surface, material)
		# No collision changes in this material-only comparison.
	setup_stair_lights(model)
	setup_actor()
	world.background_color = Color("343e42")
	motion_running = true
	stair_state(3.1, 2.)
	hud.text = ("B  接触位置旧化" if ageing_on else "A  原材料底面") + " / C 完整双跑"
	notice.text = "1 原材料  ·  2 位置旧化  ·  ↑↓ 机位  ·  空格 暂停  ·  形体与像素密度保持"
	set_view("hero")

func set_view(view: String) -> void:
	super.set_view(view)
	match view:
		"tread_contact":
			camera.size = 2.40
			camera.position = Vector3(-.7, 3.0, -.2)
			camera.look_at(Vector3(.2, 1.30, .80), Vector3.UP)
		"platform_contact":
			camera.size = 2.20
			camera.position = Vector3(2.0, 3.0, -.30)
			camera.look_at(Vector3(3.1, 1.95, .65), Vector3.UP)

func _unhandled_key_input(event: InputEvent) -> void:
	if capture_running or not event is InputEventKey or not event.pressed or event.echo: return
	if event.keycode in [KEY_1, KEY_2]:
		var old_view := view_name
		ageing_on = event.keycode == KEY_2
		show_variant("")
		set_view(old_view)
	elif event.keycode in [KEY_UP, KEY_DOWN]:
		set_view(AGE_VIEWS[posmod(AGE_VIEWS.find(view_name) + (1 if event.keycode == KEY_UP else -1), AGE_VIEWS.size())])
	elif event.keycode == KEY_SPACE: motion_running = not motion_running
	elif event.keycode == KEY_L: state_fault = not state_fault

func age_capture(filename: String, view: String, state: String) -> void:
	set_view(view)
	for frame in 3: await get_tree().process_frame
	RenderingServer.force_draw()
	var picture := get_viewport().get_texture().get_image()
	assert(picture.get_size() == VIEW)
	assert(picture.save_png(AGE_OUT + filename + ".png") == OK)
	var energies: Array[float] = []
	for bank in lights:
		for light: OmniLight3D in bank: energies.append(light.light_energy)
	var hidden: Array[String] = []
	for mesh: MeshInstance3D in stage.find_children("*", "MeshInstance3D", true, false):
		if not mesh.visible: hidden.append(str(mesh.name))
	shots.append({"file": filename + ".png", "view": view, "state": state, "aged": ageing_on,
		"resolution": [1280, 720], "camera": str(camera.global_transform), "ortho_m": camera.size,
		"keep_aspect": camera.keep_aspect, "ambient_energy": world.ambient_light_energy,
		"sun_energy": sun.light_energy, "point_energies": energies, "zone_factors": lit.duplicate(),
		"hidden_meshes": hidden, "baked_light": false, "filter": "nearest"})

func capture_all() -> void:
	capture_running = true
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(AGE_OUT))
	for aged: bool in [false, true]:
		ageing_on = aged
		show_variant("")
		motion_running = false
		stair_state(3.1, 2., true)
		for view: String in AGE_VIEWS:
			actor.visible = view in ["hero", "side", "upper", "landing"]
			await age_capture(("b_" if aged else "a_") + view, view, "neutral_material_comparison")
		state_fault = true
		stair_state(3.1, 2.)
		await age_capture(("b_" if aged else "a_") + "baseline", "hero", "minimum_0.2_fault_demo")
		state_fault = false
		stair_state(3.1, 2.)
		await age_capture(("b_" if aged else "a_") + "occupied", "hero", "occupied_zone_lighting")
	FileAccess.open(AGE_OUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify(shots, "\t"))
	print("HANDRAIL_AGE_CAPTURE_COMPLETE ", shots.size())
	get_tree().quit()
