extends SceneTree

const POD := preload("res://scenes/props/cryopod_standard_v8.tscn")
const OUTPUT := "res://docs/art/experiments/room1_pod_standard_v8/runtime_check.json"
var report := {"schema":"room1_pod_standard_v8_runtime_check_r1","loaded":false,"contract":{},"animation":{},"physics":{},"instance_isolation":{},"pass":false}
var finished_events: Array[bool] = []

func _init() -> void:
	call_deferred("go")

func go() -> void:
	var stage := Node3D.new()
	root.add_child(stage)
	var a = POD.instantiate()
	stage.add_child(a)
	var b = POD.instantiate()
	b.position = Vector3(4,0,0)
	stage.add_child(b)
	await process_frame
	await physics_frame
	await physics_frame
	report.loaded = is_instance_valid(a)
	check_contract(a)
	await check_animation(a)
	await check_isolation(a,b)
	await check_physics(stage,a)
	report.pass = report.loaded and report.contract.get("missing_nodes",[]).is_empty() and report.contract.get("has_lidopen",false) and report.animation.get("duration_valid",false) and report.animation.get("lid_moved",false) and report.animation.get("reversed",false) and report.animation.get("closed_finished_signal",false) and report.animation.get("endpoint_closed",false) and report.instance_isolation.get("independent",false) and report.physics.get("closed_lid_blocks",false) and report.physics.get("open_mattress_supports",false) and report.physics.get("open_entry_clear",false) and report.physics.get("lid_follows",false) and report.physics.get("occupied_close_protected",false) and report.physics.get("character_on_mattress",false)
	var f := FileAccess.open(OUTPUT,FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"\t")+"\n")
	f.close()
	print(JSON.stringify(report))
	quit(0 if report.pass else 1)

func check_contract(pod: Node) -> void:
	var model: Node3D = pod.get_model_root() as Node3D
	var player := find_player(model)
	var expected := [&"CryopodRoot",&"PodShell",&"PodShellEnd",&"PodShellSection",&"PodLid",&"PodLidInterior",&"PodInterior",&"PodMattress",&"PodDisplay",&"PodGlass",&"PodWindowFrame",&"PodWindowSeal",&"PodLidBacking",&"PodBasinSeal",&"PodTubeHousing_L",&"PodTubeHousing_R",&"PodTubeDiffuser_L",&"PodTubeDiffuser_R"]
	var missing: Array[String] = []
	for key in expected:
		if not find_name(model,key): missing.append(String(key))
	report.contract={"model_root":model.name if model else "","missing_nodes":missing,"has_lid_motion":find_name(model,&"LidMotion")!=null,"has_animation_player":player!=null,"has_lidopen":player!=null and player.has_animation(&"LidOpen")}

func check_animation(pod: Node) -> void:
	var model: Node3D = pod.get_model_root() as Node3D
	var player := find_player(model)
	var lid := find_name(model,&"LidMotion") as Node3D
	if not player or not player.has_animation(&"LidOpen"):
		report.animation={"error":"Missing imported LidOpen"}
		return
	var before := lid.global_position if lid else Vector3.ZERO
	pod.set_open_progress(0.0)
	pod.request_open()
	await create_timer(0.35).timeout
	var middle: StringName = pod.get_state_name()
	# Sample an explicit middle of the imported clip while it is playing. This
	# gives enough runway on slow CI/GPU frames and verifies numeric direction,
	# rather than requiring "closing" to persist for an arbitrary wall-clock wait.
	player.seek(player.get_animation(&"LidOpen").length * 0.5,true)
	var before_reverse := player.current_animation_position
	pod.request_close()
	var reverse: StringName = pod.get_state_name()
	await create_timer(0.12).timeout
	var after_reverse := player.current_animation_position
	pod.set_open_immediate(true)
	await physics_frame
	var after := lid.global_position if lid else Vector3.ZERO
	finished_events.clear()
	pod.finished.connect(finished_probe)
	pod.request_close()
	await create_timer(2.2).timeout
	var clip_length := player.get_animation(&"LidOpen").length
	report.animation={"length_seconds":clip_length,"duration_valid":absf(clip_length-1.966667)<0.05,"middle_state":middle,"reverse_state":reverse,"reverse_clip_before":before_reverse,"reverse_clip_after":after_reverse,"reversed":middle==&"opening" and reverse==&"closing" and after_reverse<before_reverse,"lid_moved":before.distance_to(after)>0.001,"endpoint_closed":pod.get_state_name()==&"closed","closed_finished_signal":finished_events.has(false)}

func check_isolation(a: Node,b: Node) -> void:
	a.set_tube_powered(false)
	a.set_screen_state("ALPHA","HOLD",0.25)
	b.set_screen_state("BRAVO","OK",0.80)
	await process_frame
	await process_frame
	var av: Variant = material_parameter(a,&"tube_powered")
	var bv: Variant = material_parameter(b,&"tube_powered")
	var screen_a: Texture2D = a.get_screen_overlay_texture() as Texture2D
	var screen_b: Texture2D = b.get_screen_overlay_texture() as Texture2D
	var hash_a: String = hash_image(screen_a)
	var hash_b: String = hash_image(screen_b)
	report.instance_isolation={"tube_a":av,"tube_b":bv,"screen_hash_a":hash_a,"screen_hash_b":hash_b,"screen_overlay_resources_independent":screen_a!=screen_b,"screen_data_independent":a.screen_name!=b.screen_name and a.screen_status!=b.screen_status,"screen_independent":screen_a!=screen_b and a.screen_name!=b.screen_name,"independent":av!=bv and screen_a!=screen_b and a.screen_name!=b.screen_name}

func check_physics(stage: Node3D,pod: Node) -> void:
	pod.set_open_immediate(false)
	await physics_frame
	var closed_hit := down_ray(stage,pod.global_position+Vector3(0,2,0))
	var lid := pod.get_node_or_null("LidCollision") as CollisionObject3D
	var closed_lid_position := lid.global_position if lid else Vector3.ZERO
	pod.set_open_immediate(true)
	await physics_frame
	var open_hit := down_ray(stage,pod.global_position+Vector3(0,2,0))
	var open_lid_position := lid.global_position if lid else Vector3.ZERO
	var mattress := pod.get_node_or_null("MattressCollision") as CollisionObject3D
	# The door opens toward +X; probe that actual side opening at bed height.
	var entry_hit := ray(stage,pod.global_position+Vector3(1.30,0.42,0),pod.global_position+Vector3(0.05,0.42,0))
	var walker := CharacterBody3D.new()
	walker.collision_layer = 2
	walker.collision_mask = 1
	var walker_shape := CollisionShape3D.new()
	var walker_capsule := CapsuleShape3D.new()
	walker_capsule.radius = 0.22
	walker_capsule.height = 1.65
	walker_shape.shape = walker_capsule
	walker.add_child(walker_shape)
	stage.add_child(walker)
	# Match the project's player capsule on the intended left access side,
	# rather than proving support with a smaller generic box at the centre.
	walker.global_position = open_hit.get("position",pod.global_position)+Vector3(-0.18,1.2,0)
	var bed_supported := false
	for step in 45:
		walker.velocity += Vector3.DOWN*0.04
		walker.move_and_slide()
		await physics_frame
		if walker.is_on_floor() and walker.get_last_slide_collision() and walker.get_last_slide_collision().get_collider()==mattress:
			bed_supported = true
			break
	walker.queue_free()
	var actor := CharacterBody3D.new()
	actor.collision_layer = 2
	var actor_shape := CollisionShape3D.new()
	var actor_box := BoxShape3D.new()
	actor_box.size = Vector3(0.35,1.2,0.35)
	actor_shape.shape = actor_box
	actor.add_child(actor_shape)
	stage.add_child(actor)
	actor.global_position = pod.global_position+Vector3(0,0.28,0)
	await physics_frame
	pod.request_close()
	await physics_frame
	var protected: bool = pod.get_state_name()!=&"closing"
	actor.queue_free()
	report.physics={"closed_lid_blocks":closed_hit.get("collider",null)==lid,"open_mattress_supports":open_hit.get("collider",null)==mattress,"character_on_mattress":bed_supported,"open_entry_clear":entry_hit.is_empty(),"entry_collider":String(entry_hit.get("collider",Node.new()).name) if not entry_hit.is_empty() else "","lid_follows":closed_lid_position.distance_to(open_lid_position)>0.001,"occupied_close_protected":protected,"lid_shape_count":lid.get_child_count() if lid else 0,"mattress_shape_count":mattress.get_child_count() if mattress else 0}

func down_ray(stage: Node3D,origin: Vector3) -> Dictionary:
	return ray(stage,origin,origin+Vector3(0,-3,0))

func ray(stage: Node3D,origin: Vector3,target: Vector3) -> Dictionary:
	return stage.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(origin,target,1))

func hash_image(texture: Texture2D) -> String:
	if not texture:return ""
	if DisplayServer.get_name() == "headless":return ""
	var image := texture.get_image()
	if not image:return ""
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(image.get_data())
	return context.finish().hex_encode()

func finished_probe(opened: bool) -> void:
	finished_events.append(opened)

func find_name(node: Node,expected: StringName) -> Node:
	if node and node.name==expected:return node
	if node:
		for child in node.get_children():
			var result := find_name(child,expected)
			if result:return result
	return null

func find_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:return node as AnimationPlayer
	for child in node.get_children():
		var result := find_player(child)
		if result:return result
	return null

func material_parameter(pod: Node,parameter: StringName) -> Variant:
	for mesh: MeshInstance3D in pod.get_model_root().find_children("*","MeshInstance3D",true,false):
		for surface in mesh.mesh.get_surface_count():
			var material := mesh.get_surface_override_material(surface)
			if material is ShaderMaterial:
				var value: Variant = (material as ShaderMaterial).get_shader_parameter(parameter)
				if value != null:return value
	return null
