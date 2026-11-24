extends SceneTree
const OUT="res://docs/art/experiments/protagonist_sprite_r5_native_r1/"
func _initialize(): capture.call_deferred()
func capture():
    var room=load("res://scenes/dev/room1_door_light_recess_b1.tscn").instantiate()
    root.add_child(room)
    for i in 20:await process_frame
    room.set_pixel_mode(0)
    room.finish_exit()
    room.review_ui.close_dialogue()
    room.teleport_player(Vector3(10.5,.05,-4.75))
    room.get_node("ReviewCamera").fov=50
    room._sync_render_camera()
    room._sync_bloom_camera()
    room.set_process(false)
    room.set_physics_process(false)
    room.info.get_parent().hide()
    var height=room.paper_hero.pixel_size*96
    for key in ["B","0","45"]:
        var path="res://docs/art/experiments/protagonist_front_c_raw_v2/B_original.png" if key=="B" else OUT+"sprite_"+key+".png"
        var img=Image.load_from_file(path)
        var bbox=img.get_used_rect()
        var tex=ImageTexture.create_from_image(img)
        for sprite in [room.paper_hero,room.bloom_paper_hero]:
            sprite.texture=tex
            sprite.hframes=1
            sprite.vframes=1
            sprite.frame=0
            sprite.texture_filter=BaseMaterial3D.TEXTURE_FILTER_NEAREST
            sprite.pixel_size=height/bbox.size.y
            sprite.position.y=(bbox.end.y-img.get_height()*.5)*sprite.pixel_size
        room._sync_paper_hero()
        room._sync_paper_lighting()
        for i in 10:await process_frame
        await RenderingServer.frame_post_draw
        var err=root.get_texture().get_image().save_png(OUT+"room_"+key+".png")
        if err!=OK:
            quit(err)
            return
    quit()
