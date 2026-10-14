@tool
extends Node3D

const ASSETS := "res://assets/art/room1_revision_20261013/"
const CUTAWAY_NAMES := ["Wall_front", "Wall_left", "Roof_hidden_for_cutaway"]
var cutaway := true
var open_pose := false
var view_index := 1
var status_label: Label

func _ready() -> void:
	_apply_cutaway()
	if Engine.is_editor_hint():
		return
	_create_overlay()
	_set_view(1)

func _unhandled_key_input(event: InputEvent) -> void:
	if Engine.is_editor_hint() or not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_1: _set_view(1)
		KEY_2: _set_view(2)
		KEY_3: _set_view(3)
		KEY_F:
			cutaway = not cutaway
			_apply_cutaway()
		KEY_L: $ReviewLights.visible = not $ReviewLights.visible
		KEY_O: _toggle_pose()
	_update_status()

func _apply_cutaway() -> void:
	var shell := get_node_or_null("Shell")
	if shell == null:
		return
	for node_name: String in CUTAWAY_NAMES:
		var object := shell.find_child(node_name, true, false) as Node3D
		if object:
			object.visible = not cutaway

func _set_view(index: int) -> void:
	view_index = index
	var camera := $ReviewCamera as Camera3D
	match index:
		1:
			camera.position = Vector3(10.5, 11.0, 16.0)
			camera.size = 25.0
			camera.look_at(Vector3(10.5, 0.9, -4.75))
		2:
			camera.position = Vector3(7.4, 3.7, -1.9)
			camera.size = 5.6
			camera.look_at(Vector3(3.525, 0.8, -7.65))
		3:
			camera.position = Vector3(10.5, 3.0, -1.0)
			camera.size = 8.0
			camera.look_at(Vector3(10.5, 1.7, -9.3))
	_update_status()

func _toggle_pose() -> void:
	var previous := $Pods/P12 as Node3D
	var pose := previous.transform
	$Pods.remove_child(previous)
	previous.queue_free()
	open_pose = not open_pose
	var filename := "pod_open_v3.glb" if open_pose else "pod_closed_v3.glb"
	var replacement := (load(ASSETS + filename) as PackedScene).instantiate() as Node3D
	replacement.name = "P12"
	replacement.transform = pose
	$Pods.add_child(replacement)

func _create_overlay() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var panel := PanelContainer.new()
	panel.position = Vector2(14, 14)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(panel)
	status_label = Label.new()
	status_label.add_theme_font_size_override("font_size", 16)
	panel.add_child(status_label)

func _update_status() -> void:
	if status_label:
		status_label.text = "Room 1 / Godot 导入审图 — 墙地待返修，灯光为试排\n1 总览 · 2 单舱 · 3 门与墙 · F 剖切/完整 · L 灯光 · O 单舱静态开盖\n镜头 %d | 剖切 %s | 灯光 %s | P12 %s（静态姿态切换）" % [view_index, cutaway, $ReviewLights.visible, "开" if open_pose else "关"]
