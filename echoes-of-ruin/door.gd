extends Area2D

var player_near = false
var opened = false

@onready var door_panel = $DoorPanel
@onready var main = get_parent()

var closed_y = 0.0
var open_offset = 180.0


func _ready():
	closed_y = door_panel.position.y

	if GameState.main_door_opened:
		opened = true
		door_panel.position.y = closed_y - open_offset


func _process(_delta):
	if player_near and Input.is_action_just_pressed("interact"):
		if opened:
			get_tree().change_scene_to_file("res://next_room.tscn")
		else:
			main.show_message("ドアはロックされている。")


func unlock_and_open():
	if opened:
		return

	opened = true
	GameState.main_door_opened = true

	main.show_message("認証完了。ドアを開放します。")

	var tween = create_tween()
	tween.tween_property(
		door_panel,
		"position:y",
		closed_y - open_offset,
		1.0
	)


func _on_body_entered(body):
	if body.name == "Player":
		player_near = true
		main.show_prompt("Eキーで調べる")


func _on_body_exited(body):
	if body.name == "Player":
		player_near = false
		main.hide_message()
