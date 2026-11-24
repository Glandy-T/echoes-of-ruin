extends Node
# Attach under the same moving character root as the model. Supply the room light switch.
const LIGHT_SHADER=preload("res://docs/art/experiments/protagonist_r5_toon_a/actor.gdshader")
var materials:Array[ShaderMaterial]=[]
var actor:Node3D
var in_room:bool
var room_controller:Node
func setup(model:Node3D,room:Node=null,direction:=Vector3(0.55,0.65,0.52)):
    actor=model
    room_controller=room
    in_room=room!=null
    for mesh in model.find_children("*","MeshInstance3D",true,false):
        for i in mesh.mesh.get_surface_count():
            var base=mesh.get_active_material(i) as StandardMaterial3D
            if base==null or base.albedo_texture==null:continue
            var material=ShaderMaterial.new()
            material.shader=LIGHT_SHADER
            material.set_shader_parameter("pigment",base.albedo_texture)
            material.set_shader_parameter("room_mode",in_room)
            material.set_shader_parameter("neutral_direction",direction)
            mesh.set_surface_override_material(i,material)
            materials.append(material)
    _process(0.0)
func _process(_dt:float):
    if not in_room or not is_instance_valid(actor):return
    var center=actor.global_position+Vector3.UP*0.70
    for material in materials:
        material.set_shader_parameter("strip_on",1.0 if room_controller.strip_on else 0.0)
        material.set_shader_parameter("actor_center",center)
