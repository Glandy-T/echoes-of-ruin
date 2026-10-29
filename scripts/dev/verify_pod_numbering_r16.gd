extends SceneTree
const POD:=preload("res://scenes/props/cryopod_standard_v8.tscn")
const FINISH:=preload("res://scripts/props/cryopod_material_variants_r16.gd")
const OUT:="res://docs/art/experiments/room1_pod_pixellab_r16/source/numbering_check.json"

func _initialize() -> void:
	call_deferred("verify")

func atlas(finish: RefCounted,role: String) -> Image:
	for entry:Dictionary in finish.entries:
		if entry.role==role:return (entry.material.get_shader_parameter("color_map") as Texture2D).get_image().duplicate() as Image
	assert(false,"Missing numbered role")
	return null

func verify() -> void:
	var world:=Node3D.new();root.add_child(world)
	var pod:=POD.instantiate();world.add_child(pod)
	for i in 3:await process_frame
	var finish:=FINISH.new(pod,12)
	var baseline:Dictionary={}
	for role in ["lid","shell_end"]:baseline[role]=atlas(finish,role)
	var labels:Dictionary={};var per_variant:Array=[]
	for variant in 4:
		finish.set_pod_number(12);finish.apply(variant,true)
		var original:Dictionary={}
		for role in ["lid","shell_end"]:original[role]=atlas(finish,role)
		var unique:Dictionary={}
		for number in range(1,21):
			finish.set_pod_number(number)
			var glyphs:Array=[]
			for role in ["lid","shell_end"]:
				var image:=atlas(finish,role);var source:Image=original[role]
				var plate:Rect2i=finish.ID_PLATES[role]
				for y in image.get_height():
					for x in image.get_width():
						if not plate.has_point(Vector2i(x,y)):assert(image.get_pixel(x,y)==source.get_pixel(x,y),"Numbering changed material pixels")
				if number==12:assert(image.get_data()==source.get_data(),"P12 changed")
				glyphs.append(image.get_region(Rect2i(finish.ID_STARTS[role],Vector2i(14,10))).get_data())
			assert(glyphs[0]==glyphs[1],"Lid/end number mismatch")
			var digest:String=glyphs[0].hex_encode().sha256_text()
			assert(not unique.has(digest),"Duplicate number plate")
			unique[digest]=number
			if variant==0:labels[number]=digest
			else:assert(labels[number]==digest,"Changing art variant changed the number")
		per_variant.append({"variant":["a","b","c","d"][variant],"unique_numbers":unique.size(),"outside_plates_exact":true,"lid_end_match":true,"P12_pixel_exact":true})
	finish.set_pod_number(12);finish.apply(0,false)
	for role in ["lid","shell_end"]:assert(atlas(finish,role).get_data()==(baseline[role] as Image).get_data(),"Old material restore changed P12")
	var old_ids:Dictionary={}
	for number in range(1,21):
		finish.set_pod_number(number)
		var glyphs:Array=[]
		for role in ["lid","shell_end"]:
			var image:=atlas(finish,role)
			if image.is_compressed():assert(image.decompress()==OK)
			image.convert(Image.FORMAT_RGBA8)
			var reference:Image=(baseline[role] as Image).duplicate()
			if reference.is_compressed():assert(reference.decompress()==OK)
			reference.convert(Image.FORMAT_RGBA8)
			var plate:Rect2i=FINISH.ID_PLATES[role]
			for y in image.get_height():
				for x in image.get_width():
					if not plate.has_point(Vector2i(x,y)):assert(image.get_pixel(x,y)==reference.get_pixel(x,y),"Old comparison material changed outside number plate")
			# P12 returns the original compressed texture without any rewriting.
			if number!=12:glyphs.append(image.get_region(Rect2i(FINISH.ID_STARTS[role],Vector2i(14,10))).get_data())
		if number!=12:
			assert(glyphs[0]==glyphs[1],"Old comparison lid/end number mismatch")
			var digest:String=glyphs[0].hex_encode().sha256_text()
			assert(not old_ids.has(digest),"Old comparison duplicate number")
			old_ids[digest]=number
	var other:=POD.instantiate();other.position=Vector3(10,0,0);world.add_child(other)
	var other_finish:=FINISH.new(other,1);other_finish.apply(0,true)
	finish.set_pod_number(20);finish.apply(3,true)
	assert(atlas(other_finish,"lid").get_region(Rect2i(FINISH.ID_STARTS["lid"],Vector2i(14,10))).get_data().hex_encode().sha256_text()==labels[1],"One pod changed another pod's ID")
	other_finish.set_pod_number(7)
	assert(atlas(finish,"shell_end").get_region(Rect2i(FINISH.ID_STARTS["shell_end"],Vector2i(14,10))).get_data().hex_encode().sha256_text()==labels[20],"Instance textures are shared incorrectly")
	var report:={"expected_sequence":"P01..P20 -> 01..20; P12 -> 12","checks":per_variant,"numbering_independent_of_art_variant":true,"old_compressed_comparison_numbering_passed":true,"two_instances_independent":true,"current_room_still_P12_only":true,"new_pixellab_calls":0}
	FileAccess.open(OUT,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("POD_NUMBERING_R16_PASS: 4 variants x 20 IDs; unique and consistent; material pixels and P12 preserved.")
	quit()
