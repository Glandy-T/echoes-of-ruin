extends SceneTree
const ROOT="res://docs/art/experiments/protagonist_r5_face_v2/"
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
    if doc.append_from_file(ROOT+"walk_pixel.glb",state)!=OK:
        quit(2)
        return
    var model=doc.generate_scene(state)
    room.player.add_child(model)
    var box=AABB()
    var mat=StandardMaterial3D.new()
    mat.texture_filter=BaseMaterial3D.TEXTURE_FILTER_NEAREST
    for mesh in model.find_children("*","MeshInstance3D",true,false):
        var local_bounds=(model.global_transform.affine_inverse()*mesh.global_transform)*mesh.get_aabb()
        box=local_bounds if not box.has_volume() else box.merge(local_bounds)
        mesh.material_override=mat
        mesh.layers |= 1 << 18
    var height=room.paper_hero.pixel_size*96.0
    var factor=height/box.size.y
    model.scale=Vector3.ONE*factor
    var view=cam.global_position-room.player.global_position
    model.rotation.y=atan2(-view.z,view.x)+deg_to_rad(22.5)
    model.position=-(model.transform.basis*Vector3(box.get_center().x,box.position.y,box.get_center().z))
    room.info.get_parent().hide()
    var anim=model.find_child("*AnimationPlayer*",true,false) as AnimationPlayer
    if anim==null or not anim.has_animation("walk"):
        push_error("Missing walk")
        quit(3)
        return
    var fill=OmniLight3D.new()
    room.add_child(fill)
    fill.global_position=room.player.global_position+Vector3(0.7,2.5,1.0)
    fill.omni_range=4.0
    fill.light_color=Color(0.84,0.91,1.0)
    fill.light_energy=0.45
    fill.light_cull_mask=1 << 18
    for size in [128]:
        var image=Image.load_from_file(ROOT+"skin.png")
        mat.albedo_texture=ImageTexture.create_from_image(image)
        for pose in ["stand","walk"]:
            if pose=="walk":
                anim.play("walk")
                anim.seek(21.0/24.0,true)
                anim.pause()
            for i in 10: await process_frame
            await RenderingServer.frame_post_draw
            var result=root.get_texture().get_image().save_png(ROOT+"room_fill_%d_%s.png"%[size,pose])
            if result!=OK:
                quit(result)
                return
            anim.stop()
    print("UV grid captured, height=",height)
    quit()



