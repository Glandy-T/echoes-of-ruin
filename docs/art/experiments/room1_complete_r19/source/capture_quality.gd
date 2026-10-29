extends Node
const BASE:="res://docs/art/experiments/room1_complete_r19/"

func _ready() -> void:call_deferred("run")

func run() -> void:
	var room:Node3D=get_parent()
	for i in 15:await get_tree().process_frame
	room.call("finish_exit");room.get("review_ui").close_dialogue()
	room.set_process(false);room.set_physics_process(false)
	(room.get("info") as Label).get_parent().hide()
	for key in ["paper_hero","bloom_paper_hero"]:room.get(key).visible=false
	room.get("review_ui").pause_button.hide()
	var camera:Camera3D=room.get_node("ReviewCamera")
	var front:MeshInstance3D=room.get_node("Shell").find_child("Wall_front",true,false)
	front.visible=true;front.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	for samples in [128,1024]:
		for raw in [true,false]:
			var label:=str(samples)+("_raw" if raw else "_denoised")
			var maps:Array=[]
			for pose in ["closed","open"]:
				if samples==128:
					maps.append(load("res://assets/art/room1_complete_r19/lighting/room_"+pose+("_raw" if raw else "")+".exr"))
				else:
					var image:=Image.load_from_file(BASE+"source/quality_probe_1024/room_"+pose+("_raw" if raw else "")+".exr")
					assert(image and not image.is_empty())
					maps.append(ImageTexture.create_from_image(image))
			for mat:ShaderMaterial in room.get("complete_shell_materials"):
				mat.set_shader_parameter("strip_irradiance",maps[0]);mat.set_shader_parameter("strip_irradiance_open",maps[1])
			for view in [
				["rear_left",Vector3(2.5,1.9,-6.2),Vector3(.2,1.45,-9.25)],
				["front_right",Vector3(18.5,1.9,-3.2),Vector3(20.8,1.45,-.25)],
				["front_middle",Vector3(10.5,2.2,3.25),Vector3(10.5,.8,-4.75)]]:
				camera.global_position=view[1];camera.look_at(view[2],Vector3.UP);camera.fov=60
				room.call("_sync_render_camera");room.call("_sync_bloom_camera");room.call("_sync_door_glow")
				for i in 12:await get_tree().process_frame
				await RenderingServer.frame_post_draw
				assert(get_viewport().get_texture().get_image().save_png(BASE+"evidence/quality_"+label+"_"+view[0]+".png")==OK)
	print("R19_QUALITY_COMPARISON_CAPTURED")
	get_tree().quit()
