extends SceneTree

# Fixed camera and fixed screen-left key light.  The actor rotates in place.
const OUTPUT := "res://docs/art/experiments/protagonist_five_idle_r1/"
const SOURCE := "res://docs/art/experiments/protagonist_r5_flat_v4/walk_pixel.glb"
const ANGLES := [0, 45, 90, 135, 180]

func _initialize() -> void:
	render_frames.call_deferred()

func render_frames() -> void:
	var viewport := SubViewport.new()
	viewport.size = Vector2i(128, 128)
	viewport.own_world_3d = true
	viewport.transparent_bg = true
	viewport.msaa_3d = Viewport.MSAA_DISABLED
	viewport.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	viewport.use_taa = false
	viewport.use_debanding = false
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)

	var document := GLTFDocument.new()
	var state := GLTFState.new()
	assert(document.append_from_file(SOURCE, state) == OK)
	var actor := document.generate_scene(state)
	viewport.add_child(actor)
	_apply_relaxed_stance(actor)
	var binder := preload("res://docs/art/experiments/protagonist_r5_toon_a/bind.gd").new()
	actor.add_child(binder)
	# The shader sees world-space normals, so this direction remains screen-left
	# while the actor turns.  It is the same neutral A-ramp used in the R5 test.
	binder.setup(actor, null, Vector3(0.55, 0.65, 0.52).normalized())

	var camera := Camera3D.new()
	viewport.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 128.0 / 125.0
	var target := Vector3(0.0, 0.50 + 0.5 / 125.0, 0.0)
	camera.position = target + Vector3(2.0, 0.0, 0.0)
	camera.look_at(target)

	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("#343939")
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color.WHITE
	environment.ambient_light_energy = 0.40
	camera.environment = environment

	var key := DirectionalLight3D.new()
	viewport.add_child(key)
	# This stays in the camera's screen-left world direction for every frame.
	key.look_at(Vector3(-0.55, -0.65, -0.52).normalized())
	key.light_energy = 0.85

	for angle in ANGLES:
		actor.rotation = Vector3(0.0, deg_to_rad(-angle), 0.0)
		for _frame in 8:
			await process_frame
		await RenderingServer.frame_post_draw
		var result := viewport.get_texture().get_image().save_png(OUTPUT + "input_%d.png" % angle)
		if result != OK:
			quit(result)
			return
	quit()

func _apply_relaxed_stance(actor: Node3D) -> void:
	var skeletons := actor.find_children("*", "Skeleton3D", true, false)
	assert(skeletons.size() == 1)
	var skeleton := skeletons[0] as Skeleton3D
	# The offset is deliberately small. It separates the feet without changing
	# the rig's knees, ankles, clothing, or the approved body proportion.
	# The near leg is the load-bearing one.  The opposite leg gets a wider,
	# relaxed placement so five rotations do not read as a mannequin T-pose.
	for spec in [["L_Thigh", -0.014], ["R_Thigh", 0.006]]:
		var bone := skeleton.find_bone(spec[0])
		assert(bone >= 0)
		var position := skeleton.get_bone_pose_position(bone)
		position.x += spec[1]
		skeleton.set_bone_pose_position(bone, position)
