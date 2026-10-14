extends SceneTree

const ASSETS := "res://assets/art/room1_revision_20261013/"
const OUTPUT := "res://scenes/dev/room1_import_review_r1.tscn"

func _initialize() -> void:
	var root := Node3D.new()
	root.name = "Room1ImportReview"
	root.set_script(load("res://scripts/dev/room1_import_review.gd"))
	get_root().add_child(root)
	var shell := (load(ASSETS + "room1_shell_full_r1.glb") as PackedScene).instantiate()
	shell.name = "Shell"
	add_owned(root, shell, root)
	var pods := Node3D.new()
	pods.name = "Pods"
	add_owned(root, pods, root)
	var placements: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ASSETS + "pod_placement_godot.json"))
	var closed := load(ASSETS + "pod_closed_v3.glb") as PackedScene
	for entry: Dictionary in placements.placements:
		var pod := closed.instantiate() as Node3D
		pod.name = entry.id
		var xyz: Array = entry.position_godot_m
		pod.position = Vector3(xyz[0], xyz[1], xyz[2])
		pod.rotation.y = entry.rotation_y_radians
		add_owned(pods, pod, root)
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("242c32")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("a7b9c6")
	environment.ambient_light_energy = 0.35
	var world := WorldEnvironment.new()
	world.name = "WorldEnvironment"
	world.environment = environment
	add_owned(root, world, root)
	var lights := Node3D.new()
	lights.name = "ReviewLights"
	add_owned(root, lights, root)
	# Light proxies approximate ceiling strips; these are review settings, not final lighting.
	for row in 2:
		for column in 4:
			var light := OmniLight3D.new()
			light.name = "StripProxy_%s_%s" % [row, column]
			light.position = Vector3(2.5 + column * 5.3, 2.85, -0.8 if row == 0 else -8.7)
			light.light_color = Color("ccdde4")
			light.light_energy = 0.2
			light.omni_range = 7.0
			light.omni_attenuation = 1.4
			light.shadow_enabled = false
			add_owned(lights, light, root)
	var fill := DirectionalLight3D.new()
	fill.name = "ReviewFill"
	fill.rotation_degrees = Vector3(-60, -25, 0)
	fill.light_color = Color("e2e5da")
	fill.light_energy = 0.45
	fill.shadow_enabled = true
	add_owned(lights, fill, root)
	var camera := Camera3D.new()
	camera.name = "ReviewCamera"
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.keep_aspect = Camera3D.KEEP_WIDTH
	camera.size = 25.0
	camera.near = 0.1
	camera.far = 100.0
	camera.current = true
	add_owned(root, camera, root)
	camera.position = Vector3(10.5, 11.0, 16.0)
	camera.basis = Basis.looking_at(Vector3(10.5, 0.9, -4.75) - camera.position)
	var packed := PackedScene.new()
	var error := packed.pack(root)
	if error == OK:
		error = ResourceSaver.save(packed, OUTPUT)
	print("ROOM1_BUILD: ", OUTPUT, " error=", error, " pods=", pods.get_child_count())
	root.queue_free()
	quit(error)

func add_owned(parent: Node, child: Node, owner_node: Node) -> void:
	parent.add_child(child)
	child.owner = owner_node
