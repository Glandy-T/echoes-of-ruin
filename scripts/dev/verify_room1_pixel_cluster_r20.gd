extends Node

const REPORT := "res://docs/art/experiments/room1_pixel_cluster_r20/source/runtime_validation.json"
const REVIEW_ROOT := "res://assets/art/room1_pixel_cluster_r20/"
var room: Node3D
var errors: Array[String] = []
var checks := {}
var baseline := {}

func _ready() -> void: call_deferred("run")
func check(label: String, passed: bool) -> void:
	checks[label] = passed
	if not passed:
		errors.append(label)
		push_error("R20_CHECK "+label)
func frames(count: int) -> void:
	for _i in count: await get_tree().physics_frame
func node_state() -> Dictionary:
	var result := {}
	for node: Node in room.find_children("*", "Node3D", true, false):
		if node is MeshInstance3D or node is CollisionObject3D:
			var mesh_path: String = (node.mesh.resource_path if node is MeshInstance3D and node.mesh else "")
			result[str(node.get_path())] = {"transform":node.global_transform,"mesh":mesh_path,"layer":node.collision_layer if node is CollisionObject3D else -1,"mask":node.collision_mask if node is CollisionObject3D else -1}
	return result
func unchanged_nodes(label: String) -> void:
	var now:=node_state()
	check(label+"_node_set",now.keys().size()==baseline.nodes.keys().size())
	for key in baseline.nodes:
		check(label+"_"+key+"_transform",now.has(key) and now[key].transform.is_equal_approx(baseline.nodes[key].transform))
		check(label+"_"+key+"_mesh",now.has(key) and now[key].mesh==baseline.nodes[key].mesh)
		check(label+"_"+key+"_collision",now.has(key) and now[key].layer==baseline.nodes[key].layer and now[key].mask==baseline.nodes[key].mask)
func unchanged_other_pods(label: String) -> void:
	for id in room.room_pods:
		if id=="P12":continue
		var pod:Node3D=room.room_pods[id]
		check(label+"_"+id+"_lightmaps",pod.closed_irradiance.resource_path==baseline.lights[id].closed and pod.open_irradiance.resource_path==baseline.lights[id].open)

func run() -> void:
	room=get_parent() as Node3D
	await frames(12)
	room.finish_exit()
	room.review_ui.close_dialogue()
	baseline.nodes=node_state()
	baseline.lights={}
	for id in room.room_pods:
		var pod:Node3D=room.room_pods[id]
		baseline.lights[id]={"closed":pod.closed_irradiance.resource_path,"open":pod.open_irradiance.resource_path}
	room.set_cluster_mode(1)
	var a:Dictionary=room.get_cluster_review_report()
	check("A_baseline",a.mode==1)
	for path in a.pod_maps.values():check("A_p12_not_r20_"+str(path),not str(path).begins_with(REVIEW_ROOT))
	for path in a.wall_maps:check("A_wall_not_r20_"+str(path),not str(path).begins_with(REVIEW_ROOT))
	unchanged_nodes("A")
	unchanged_other_pods("A")
	room.set_cluster_mode(2)
	var b:Dictionary=room.get_cluster_review_report()
	check("B_mode",b.mode==2)
	check("B_wall",b.wall_maps.all(func(path):return path==REVIEW_ROOT+"wall_left.png"))
	check("B_pod",b.pod_maps=={"lid":REVIEW_ROOT+"pod_lid.png","shell_side":REVIEW_ROOT+"pod_shell_side.png","shell_end":REVIEW_ROOT+"pod_shell_end.png"})
	unchanged_nodes("B")
	unchanged_other_pods("B")
	room.set_cluster_mode(3)
	var c:Dictionary=room.get_cluster_review_report()
	check("C_mode_and_maps",c.mode==3 and c.wall_maps==b.wall_maps and c.pod_maps==b.pod_maps)
	unchanged_nodes("C")
	unchanged_other_pods("C")
	room.set_cluster_mode(1)
	var restored:Dictionary=room.get_cluster_review_report()
	check("A_restored",restored.mode==1 and restored.pod_maps==a.pod_maps and restored.wall_maps==a.wall_maps)
	unchanged_nodes("A_restored")
	unchanged_other_pods("A_restored")
	var report={"result":"PASS" if errors.is_empty() else "FAIL","errors":errors,"checks":checks,"scope":"r20 changes only one left-wall bay and P12 three exterior color maps; geometry, transforms, UVs, collision, r19 lightmaps and other pods remain r19"}
	FileAccess.open(REPORT,FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print("R20_CLUSTER_RUNTIME ",report.result," checks=",checks.size()," errors=",JSON.stringify(errors))
	get_tree().quit(0 if errors.is_empty() else 1)
