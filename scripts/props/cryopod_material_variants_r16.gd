extends RefCounted

const ROOT := "res://assets/art/room1_pod_pixellab_r16/"
const ROLES := {
	"PodLid":"lid", "PodShell":"shell_side", "PodShellEnd":"shell_end",
	"PodInterior":"interior", "PodLidInterior":"interior", "PodMattress":"mattress",
	"PodLidBacking":"section", "PodWindowFrame":"section", "PodWindowSeal":"section",
	"PodBasinSeal":"section", "PodDisplayHousing":"section", "PodShellSection":"section"
}
var entries:Array[Dictionary]=[]
var enabled:=true
var variant:=0
var cache:Dictionary={}

func _init(pod: Node3D) -> void:
	for mesh: MeshInstance3D in pod.get_model_root().find_children("*","MeshInstance3D",true,false):
		if not ROLES.has(str(mesh.name)):continue
		for surface in mesh.mesh.get_surface_count():
			var material:=mesh.get_active_material(surface) as ShaderMaterial
			assert(material and material.shader.resource_path=="res://scripts/props/cryopod_standard_v8_surface.gdshader")
			entries.append({"mesh":str(mesh.name),"surface":surface,"role":ROLES[str(mesh.name)],"material":material,"baseline":material.get_shader_parameter("color_map")})
	assert(entries.size()==12,"Expected twelve textured solid surfaces, excluding glass, screen and all four tube parts.")

func apply(index: int, active: bool=true) -> void:
	variant=posmod(index,4);enabled=active
	for entry in entries:
		var texture:Texture2D=entry.baseline
		if active:
			var key:String=entry.role
			var folder: String=("variant_"+["a","b","c","d"][variant]) if key in ["lid","shell_side","shell_end"] else "shared"
			var path:=ROOT+folder+"/"+key+".png"
			if not cache.has(path):cache[path]=load(path)
			texture=cache[path] as Texture2D
			assert(texture,"Missing PixelLab pod surface: "+path)
		(entry.material as ShaderMaterial).set_shader_parameter("color_map",texture)

func bindings() -> Array:
	var result:=[]
	for entry in entries:
		var material:ShaderMaterial=entry.material
		result.append({"mesh":entry.mesh,"role":entry.role,"texture":(material.get_shader_parameter("color_map") as Texture2D).resource_path,"shader":material.shader.resource_path,"baked_energy":material.get_shader_parameter("baked_energy"),"closed_irradiance":(material.get_shader_parameter("closed_irradiance") as Texture2D).resource_path,"open_irradiance":(material.get_shader_parameter("open_irradiance") as Texture2D).resource_path})
	return result
