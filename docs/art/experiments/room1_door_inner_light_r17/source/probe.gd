extends SceneTree
func _initialize()->void:call_deferred("probe")
func probe()->void:
	var room:Node3D=(load("res://scenes/dev/room1_pod_pixellab_r16.tscn") as PackedScene).instantiate();root.add_child(room)
	for i in 12:await process_frame
	var panel:MeshInstance3D=room.door_mesh
	print("DOOR_CENTER ",room.door_closed_position," AABB ",panel.get_aabb()," ROOT ",room.integrated_root.global_transform)
	for part:MeshInstance3D in room.integrated_root.find_children("JambLight_*","MeshInstance3D",true,false):print(part.name," world=",part.global_transform," aabb=",part.get_aabb())
	print("GAME_CAMERA ",room.get_node("ReviewCamera").global_transform)
	var back:Node3D=room.find_child("BlackDoorway",true,false)
	if back:print("BACKDROP ",back.global_transform)
	quit()
