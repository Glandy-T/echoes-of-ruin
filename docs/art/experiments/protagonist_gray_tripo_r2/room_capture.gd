extends SceneTree
const ROOT="res://docs/art/experiments/protagonist_gray_tripo_r2/"
func _initialize():
    go.call_deferred()
func go():
    var room=load("res://scenes/dev/room1_door_light_recess_b1.tscn").instantiate()
    root.add_child(room)
    for i in 20: await process_frame
    room.set_pixel_mode(0)
    room.finish_exit()
    room.review_ui.close_dialogue()
    room.teleport_player(Vector3(10.5,0.05,-4.75))
    var cam=room.get_node("ReviewCamera")
    cam.fov=50
    room._sync_render_camera()
    room._sync_bloom_camera()
    room.set_process(false)
    room.set_physics_process(false)
    room.paper_hero.hide()
    room.bloom_paper_hero.hide()
    var doc=GLTFDocument.new()
    var state=GLTFState.new()
    if doc.append_from_file(ROOT+"original.glb",state)!=OK:
        quit(2)
        return
    var model=doc.generate_scene(state)
    room.player.add_child(model)
    var box=AABB()
    var mat=StandardMaterial3D.new()
    mat.albedo_color=Color(0.65,0.65,0.65)
    for mesh in model.find_children("*","MeshInstance3D",true,false):
        var local_bounds=(model.global_transform.affine_inverse()*mesh.global_transform)*mesh.get_aabb()
        box=local_bounds if not box.has_volume() else box.merge(local_bounds)
        mesh.material_override=mat
    var height=room.paper_hero.pixel_size*96.0
    var factor=height/box.size.y
    model.scale=Vector3.ONE*factor
    var view=cam.global_position-room.player.global_position
    model.rotation.y=atan2(-view.z,view.x)+deg_to_rad(22.5)
    model.position=-(model.transform.basis*Vector3(box.get_center().x,box.position.y,box.get_center().z))
    room.info.get_parent().hide()
    for i in 24: await process_frame
    await RenderingServer.frame_post_draw
    var result=root.get_texture().get_image().save_png(ROOT+"room.png")
    print("GRAY_ROOM height=",height," result=",result)
    quit(result)
