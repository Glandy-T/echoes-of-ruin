extends Node2D

@onready var ui = $UI

func show_message(text: String, duration: float = 2.5):
	ui.show_text(text, duration)

func show_prompt(text: String):
	ui.show_prompt(text)

func hide_message():
	ui.hide_text()
