extends SceneTree

# Fixed camera and fixed screen-left key light.  The actor rotates in place.
const OUTPUT := "res://docs/art/experiments/protagonist_walk_side_r1/"
const SOURCE := "res://docs/art/experiments/protagonist_walk_r5_hem_fix/walk.glb"
const SOURCE_FRAMES := [9.0, 12.5, 16.0, 19.5, 23.0, 26.5, 30.0, 33.5]

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
	actor.rotation.y = deg_to_rad(-90.0)
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

	var player := actor.find_child("AnimationPlayer", true, false) as AnimationPlayer
	var skeleton := actor.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	assert(player != null and skeleton != null)
	var hip_index := skeleton.find_bone("Pelvis")
	var clip := player.get_animation_list()[0]
	player.play(clip)
	player.pause()
	for i in SOURCE_FRAMES.size():
		player.seek(SOURCE_FRAMES[i] / 24.0, true)
		skeleton.force_update_all_bone_transforms()
		# Remove only the forward root travel. Bob and limb motion stay in the pose.
		actor.position = Vector3.ZERO
		var hip := skeleton.to_global(skeleton.get_bone_global_pose(hip_index).origin)
		actor.position.z = -hip.z
		for _frame in 8:
			await process_frame
		await RenderingServer.frame_post_draw
		var result := viewport.get_texture().get_image().save_png(OUTPUT + "render_%02d.png" % (i + 1))
		if result != OK:
			quit(result)
			return
	quit()
