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
var numbered_cache:Dictionary={}
var pod_number:int
const DIGITS := ["111101101101111","010110010010111","110001010100111","111001111001111","101101111001001","111100111001111","111100111101111","111001001001001","111101111101111","111101111001111"]
const ID_PLATES := {"lid":Rect2i(47,197,33,14),"shell_end":Rect2i(55,35,18,14)}
const ID_STARTS := {"lid":Vector2i(55,198),"shell_end":Vector2i(57,37)}

func _init(pod: Node3D, number: int) -> void:
	assert(number>=1 and number<=20,"Room 1 pod number must be explicitly supplied as 1..20.")
	pod_number=number
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
		if entry.role in ID_PLATES:
			(entry.material as ShaderMaterial).set_shader_parameter("color_map",_with_number(texture,entry.role))

func set_pod_number(number: int) -> void:
	assert(number>=1 and number<=20,"Room 1 pod number must be 1..20.")
	pod_number=number
	apply(variant,enabled)

func _with_number(texture: Texture2D, role: String) -> Texture2D:
	# P12 is already correct in all approved sample atlases; keep it pixel-exact.
	if pod_number==12:return texture
	var key:=str(texture.get_instance_id())+":"+role+":"+str(pod_number)
	if numbered_cache.has(key):return numbered_cache[key]
	var image:=texture.get_image().duplicate() as Image
	image.fill_rect(ID_PLATES[role],Color8(190,199,194))
	var start:Vector2i=ID_STARTS[role]
	var label:="%02d"%pod_number
	for i in 2:
		var pattern:String=DIGITS[int(label.substr(i,1))]
		for y in 5:
			for x in 3:
				if pattern[y*3+x]=="1":image.fill_rect(Rect2i(start+Vector2i(i*8+x*2,y*2),Vector2i(2,2)),Color8(34,51,64))
	var result:=ImageTexture.create_from_image(image)
	result.resource_name="R16_%02d_%s"%[pod_number,role]
	result.set_meta("source_texture_path",texture.resource_path)
	numbered_cache[key]=result
	return result

func bindings() -> Array:
	var result:=[]
	for entry in entries:
		var material:ShaderMaterial=entry.material
		var texture:=material.get_shader_parameter("color_map") as Texture2D
		result.append({"mesh":entry.mesh,"role":entry.role,"pod_number":pod_number,"texture":texture.resource_path,"source_texture":texture.get_meta("source_texture_path",texture.resource_path),"shader":material.shader.resource_path,"baked_energy":material.get_shader_parameter("baked_energy"),"closed_irradiance":(material.get_shader_parameter("closed_irradiance") as Texture2D).resource_path,"open_irradiance":(material.get_shader_parameter("open_irradiance") as Texture2D).resource_path})
	return result
