extends "res://scripts/dev/capture_cryo_4f_complete_v3.gd"

func run() -> void:
	level=get_parent();await frames(80);level.finish_exit();level.review_ui.close_dialogue()
	level.set_process(false);level.set_physics_process(false);level.test_mode=true
	level.info.get_parent().hide();level.paper_hero.hide();level.door_glow_overlay.hide();level.bloom_overlay.hide()
	level.room_wall_occlusion_enabled=false;level._update_occlusion()
	var camera := level.get_node("ReviewCamera") as Camera3D
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.keep_aspect=Camera3D.KEEP_WIDTH;camera.far=300
	# Eight corridors, both facing walls, eight overlapping sections per wall.
	# Camera stays in the aisle; opaque opposite wall is behind the camera.
	for raw in [true,false]:
		level.set_corridor_raw(raw)
		var prefix := "tech_raw" if raw else "tech_denoised"
		for i in 8:
			var r: Array=level.floor_layout.walk_rects[i]
			for side in [-1,1]:
				for part in 8:
					var x: float=lerpf(r[0],r[2],(part+.5)/8.0)
					var z: float=4.2-(r[1]+r[3])*.5
					camera.size=(r[2]-r[0])/8.0+.35;camera.position=Vector3(x,1.7,z)
					camera.look_at(Vector3(x,1.7,z+side),Vector3.UP)
					await shot("%s_c%d_s%d_p%d"%[prefix,i,side,part],3)
		# Floor only: remove walls for inspection, actual floor remains untouched.
		var hidden: Array[Node3D]=[]
		for mesh in level.corridor_sample.find_children("*","MeshInstance3D",true,false):
			if level.floor_layout.receivers.get(str(mesh.name),{}).get("kind","")!="floor" and mesh.visible:mesh.hide();hidden.append(mesh)
		for i in 8:
			var r: Array=level.floor_layout.walk_rects[i]
			for part in 4:
				var x: float=lerpf(r[0],r[2],(part+.5)/4.0);var z: float=4.2-(r[1]+r[3])*.5
				camera.size=(r[2]-r[0])/4.0+.35;camera.position=Vector3(x,10,z)
				camera.look_at(Vector3(x,0,z),Vector3.FORWARD)
				await shot("%s_floor_c%d_p%d"%[prefix,i,part],3)
		for mesh in hidden:mesh.show()
	FileAccess.open(OUT+"technical_capture_record.json",FileAccess.WRITE).store_string(JSON.stringify(records,"\t"))
	get_tree().quit()
