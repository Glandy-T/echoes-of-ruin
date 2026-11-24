extends SceneTree
const OUT="res://docs/art/experiments/protagonist_sprite_r5_native_r1/"
func _initialize(): render_frames.call_deferred()
func render_frames():
    var vp=SubViewport.new()
    vp.size=Vector2i(128,128)
    vp.own_world_3d=true
    vp.transparent_bg=true
    vp.msaa_3d=Viewport.MSAA_DISABLED
    vp.screen_space_aa=Viewport.SCREEN_SPACE_AA_DISABLED
    vp.use_taa=false
    vp.use_debanding=false
    vp.scaling_3d_scale=1.0
    vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS
    root.add_child(vp)
    var doc=GLTFDocument.new()
    var state=GLTFState.new()
    if doc.append_from_file("res://docs/art/experiments/protagonist_r5_flat_v4/walk_pixel.glb",state)!=OK:
        quit(2)
        return
    var model=doc.generate_scene(state)
    vp.add_child(model)
    var binder=preload("res://docs/art/experiments/protagonist_r5_toon_a/bind.gd").new()
    model.add_child(binder)
    binder.setup(model,null,Vector3(.55,.65,.52).normalized())
    assert(binder.materials.size()==3)
    var cam=Camera3D.new()
    vp.add_child(cam)
    cam.projection=Camera3D.PROJECTION_ORTHOGONAL
    cam.size=128.0/117.0
    var target=Vector3(0,.5+.5/117.0,0)
    for angle in [0,45]:
        cam.position=target+Vector3.RIGHT.rotated(Vector3.UP,deg_to_rad(angle))*2
        cam.look_at(target)
        for i in 4:await process_frame
        await RenderingServer.frame_post_draw
        var err=vp.get_texture().get_image().save_png(OUT+"raw_%d.png"%angle)
        if err!=OK:
            quit(err)
            return
    quit()

