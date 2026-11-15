extends "res://scripts/dev/cryo_building_review_v1.gd"
## One-flight gray comparison. All samples share lighting and camera settings.

const SAMPLE_ROOT := "res://assets/art/cryo_handrail_integrated_v1/"
const SAMPLE_OUTPUT := "res://docs/art/experiments/cryo_handrail_integrated_v1/evidence/"
const SAMPLE_IDS := ["A", "B", "C"]
const SAMPLE_VIEWS := ["overview", "grip", "turn", "hero"]
var sample_id := "A"
var gray_material: StandardMaterial3D

func mat(_name: String, _distant := false) -> StandardMaterial3D:
	if gray_material == null:
		gray_material = StandardMaterial3D.new()
		gray_material.albedo_color = Color("919794")
		gray_material.roughness = .90
		gray_material.metallic_specular = .12
	return gray_material

func import_asset(file: String, distant := false) -> Node3D:
	if file != "HR-A":
		return super.import_asset(file, distant)
	var packed := load(SAMPLE_ROOT + "HR_" + sample_id + "_gray.glb") as PackedScene
	assert(packed != null)
	var model := packed.instantiate() as Node3D
	stage.add_child(model)
	for mesh_node: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		for surface in mesh_node.mesh.get_surface_count():
			mesh_node.set_surface_override_material(surface, mat("gray"))
	return model

func show_variant(id: String) -> void:
	sample_id = id if SAMPLE_IDS.has(id) else "A"
	super.show_variant("HR-A")
	candidate = "HR-" + sample_id
	motion_running = false
	stair_state(3.1, 2., true)
	for bank in lights:
		for light: OmniLight3D in bank:
			light.light_energy *= .40
	actor.visible = false
	hud.text = ["A  杆件护栏", "B  折板护栏", "C  一体化握持槽"][SAMPLE_IDS.find(sample_id)]
	notice.text = "轮廓灰模  ·  1 / 2 / 3 对比  ·  ↑↓ 视角  ·  单跑与折返截段"
	set_view("overview")

func set_view(view: String) -> void:
	view_name = view
	# The same technical cut shows the single lower flight in every sample.
	for pattern: String in ["L01_*", "EntryWall*"]:
		for node in stage.find_children(pattern, "MeshInstance3D", true, false):
			node.visible = view == "hero"
	for pattern: String in ["Upper_*", "FloorLanding", "L01_ZONE_UPPER*", "L01_ZONE_FLOOR*", "L01_TURN_UPPER_RETURN*"]:
		for node in stage.find_children(pattern, "MeshInstance3D", true, false):
			node.visible = false
	for node in stage.find_children("K01_LevelSign", "MeshInstance3D", true, false):
		node.visible = view == "hero"
	for label in stage.find_children("*", "Label3D", true, false):
		label.visible = view == "hero"
	var view_position := Vector3(-.60, 3.70, 3.40)
	var target := Vector3(.25, 1.60, -.40)
	var size := 3.60
	match view:
		"grip":
			view_position = Vector3(-.05, 2.40, 1.50)
			target = Vector3(.10, 1.90, -.90)
			size = 1.35
		"turn":
			view_position = Vector3(3.40, 3.80, .75)
			target = Vector3(1.55, 2.60, -.90)
			size = 1.90
		"hero":
			view_position = Vector3(-7.10, 5.90, -1.45)
			target = Vector3(.45, 2.50, -1.0)
			size = 7.65
			actor.visible = true
	camera.size = size
	camera.position = view_position
	camera.look_at(target, Vector3.UP)

func _unhandled_key_input(event: InputEvent) -> void:
	if capture_running or not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode >= KEY_1 and event.keycode <= KEY_3:
		show_variant(SAMPLE_IDS[event.keycode - KEY_1])
	elif event.keycode in [KEY_UP, KEY_DOWN]:
		var offset := 1 if event.keycode == KEY_UP else -1
		actor.visible = false
		set_view(SAMPLE_VIEWS[posmod(SAMPLE_VIEWS.find(view_name) + offset, SAMPLE_VIEWS.size())])

func capture_all() -> void:
	capture_running = true
	motion_running = false
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SAMPLE_OUTPUT))
	for id: String in SAMPLE_IDS:
		show_variant(id)
		for view: String in SAMPLE_VIEWS:
			actor.visible = false
			set_view(view)
			for frame in 3:
				await get_tree().process_frame
			RenderingServer.force_draw()
			var picture := get_viewport().get_texture().get_image()
			assert(picture.get_size() == VIEW)
			var filename := id.to_lower() + "_" + view + ".png"
			assert(picture.save_png(SAMPLE_OUTPUT + filename) == OK)
			var point_lights: Array[float] = []
			for bank in lights:
				for light: OmniLight3D in bank:
					point_lights.append(light.light_energy)
			shots.append({
				"file": filename, "sample": id, "view": view,
				"resolution": [1280, 720], "camera": str(camera.global_transform),
				"ortho_m": camera.size, "light_energy": sun.light_energy,
				"ambient_energy": world.ambient_light_energy,
				"zone_factors": lit.duplicate(),
				"point_light_energies": point_lights,
				"albedo": "same gray for all geometry",
				"cut": "single lower flight and return at shaft centre",
			})
	FileAccess.open(SAMPLE_OUTPUT + "capture_record.json", FileAccess.WRITE).store_string(JSON.stringify(shots, "\t"))
	print("INTEGRATED_HANDRAIL_CAPTURE_COMPLETE ", shots.size())
	get_tree().quit()
