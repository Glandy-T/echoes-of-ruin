extends Node3D
## Standalone material review; no gameplay, route, lighting-trigger or existing scene changes.

const OUT := "res://docs/art/experiments/cryo_stair_material_sample_v1/evidence/"
const MODEL := "res://assets/art/cryo_stair_material_sample_v1/stair_material_sample_v1.glb"
var camera: Camera3D
var sample: Node3D
var original_materials: Dictionary = {}
var records: Array = []

func _ready() -> void:
	get_window().size = Vector2i(1280,720)
	var world := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("252e31")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("e0e5e2")
	env.ambient_light_energy = 0.25
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	world.environment = env
	add_child(world)
	var key := DirectionalLight3D.new()
	key.name = "TEMP_Review_Key_NOT_Final_Stair_Lighting"
	key.rotation_degrees = Vector3(-58,-28,0)
	key.light_color = Color("f1f3ef")
	key.light_energy = 0.55
	key.shadow_enabled = true
	add_child(key)
	sample = load(MODEL).instantiate()
	add_child(sample)
	collect_materials(sample)
	camera = Camera3D.new()
	camera.near = 0.05
	camera.far = 100
	camera.fov = 48
	camera.current = true
	add_child(camera)
	set_view(0)
	if "--capture-stair" in OS.get_cmdline_user_args(): call_deferred("capture")

func collect_materials(node: Node) -> void:
	if node is MeshInstance3D:
		var mesh := node as MeshInstance3D
		for i in mesh.mesh.get_surface_count():
			var mat := mesh.get_active_material(i)
			if mat is StandardMaterial3D:
				mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
				mat.roughness = 0.95
				mat.metallic = 0
				mat.metallic_specular = 0.05
			original_materials[str(mesh.get_path())+":"+str(i)] = mat
	for child in node.get_children(): collect_materials(child)

func set_gray(node: Node, enabled: bool) -> void:
	if node is MeshInstance3D:
		var mesh := node as MeshInstance3D
		for i in mesh.mesh.get_surface_count():
			if enabled:
				var gray := StandardMaterial3D.new()
				gray.albedo_color = Color("7c8380")
				gray.roughness = 0.95
				gray.metallic_specular = 0.05
				mesh.set_surface_override_material(i,gray)
			else: mesh.set_surface_override_material(i,original_materials[str(mesh.get_path())+":"+str(i)])
	for child in node.get_children(): set_gray(child,enabled)

func set_view(index: int) -> void:
	match index:
		0:
			camera.position = Vector3(5.3,4.7,5.1)
			camera.look_at(Vector3(-0.05,1.05,-1.45))
		1:
			camera.position = Vector3(3.1,2.0,1.6)
			camera.look_at(Vector3(0.85,0.65,-1.35))
		2:
			camera.position = Vector3(4.4,5.4,-0.2)
			camera.look_at(Vector3(-0.15,1.9,-3.9))

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_1: set_view(0)
		if event.keycode == KEY_2: set_view(1)
		if event.keycode == KEY_3: set_view(2)
		if event.keycode == KEY_ESCAPE: get_tree().quit()

func shot(label: String, view: int) -> void:
	set_view(view)
	for i in 16: await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image()
	assert(image.get_size() == Vector2i(1280,720))
	assert(image.save_png(OUT+label+".png") == OK)
	records.append({"file":label+".png","position":str(camera.position),"transform":str(camera.global_transform),"fov":camera.fov,"resolution":[1280,720],"lighting":"temporary neutral realtime review; not final motion lighting"})
	print("STAIR_SHOT ",label)

func capture() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	set_gray(sample,true)
	await shot("gray_overview",0)
	set_gray(sample,false)
	await shot("material_overview",0)
	await shot("material_treads",1)
	await shot("material_landing",2)
	# Same UV density/camera/light, one optional coarser PixelLab candidate.
	var variant := load("res://assets/art/cryo_stair_material_sample_v1/mineral_b.png") as Texture2D
	for node in sample.find_children("*","MeshInstance3D",true,false):
		var mesh := node as MeshInstance3D
		for i in mesh.mesh.get_surface_count():
			var mat := mesh.get_active_material(i) as StandardMaterial3D
			if mat and "Mineral_A" in mat.resource_name:
				var alternate := mat.duplicate() as StandardMaterial3D
				alternate.albedo_texture = variant
				mesh.set_surface_override_material(i,alternate)
	await shot("candidate_b_overview",0)
	FileAccess.open(OUT+"capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
