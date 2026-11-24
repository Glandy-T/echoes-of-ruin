extends SceneTree
const ROOT="res://docs/art/experiments/protagonist_r5_toon_a/"
func _initialize():go.call_deferred()
func go():
    var stage=Node3D.new()
    root.add_child(stage)
    var doc=GLTFDocument.new()
    var state=GLTFState.new()
    if doc.append_from_file("res://docs/art/experiments/protagonist_r5_flat_v4/walk_pixel.glb",state)!=OK:
        quit(2)
        return
    var model=doc.generate_scene(state)
    stage.add_child(model)
    var camera=Camera3D.new()
    stage.add_child(camera)
    var target=Vector3(0,0.50,0)
    camera.position=target+Vector3(2,0,0.15)
    camera.look_at(target)
    camera.projection=Camera3D.PROJECTION_ORTHOGONAL
    camera.size=1.10
    var env=Environment.new()
    env.background_mode=Environment.BG_COLOR
    env.background_color=Color("#343939")
    env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color=Color.WHITE
    env.ambient_light_energy=0.40
    camera.environment=env
    var key=DirectionalLight3D.new()
    stage.add_child(key)
    var direction=Vector3(.55,.65,.52).normalized()
    key.look_at(-direction)
    key.light_energy=0.85
    for variant in ["before","after"]:
        if variant=="after":
            var binder=preload("res://docs/art/experiments/protagonist_r5_toon_a/bind.gd").new()
            model.add_child(binder)
            binder.setup(model,null,direction)
        for i in 5:await process_frame
        await RenderingServer.frame_post_draw
        var result=root.get_texture().get_image().save_png(ROOT+variant+"_neutral.png")
        if result!=OK:
            quit(result)
            return
    quit()
