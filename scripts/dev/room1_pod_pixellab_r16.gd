extends "res://scripts/dev/room1_floor_variants_r15.gd"

const POD_FINISH := preload("res://scripts/props/cryopod_material_variants_r16.gd")
var pod_finish:RefCounted
var pod_finish_on:=true
var pod_variant:=0

func _ready() -> void:
	super._ready()
	pod_finish=POD_FINISH.new(standard,12)
	set_pod_finish(0,true)

func set_pod_finish(index: int, enabled: bool=true) -> void:
	pod_variant=posmod(index,4);pod_finish_on=enabled
	if pod_finish:pod_finish.apply(pod_variant,enabled)
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode==KEY_P:
			set_pod_finish(pod_variant,not pod_finish_on);get_viewport().set_input_as_handled();return
		if event.physical_keycode==KEY_K:
			set_pod_finish(pod_variant+1,true);get_viewport().set_input_as_handled();return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		info.text="Room 1 / 单舱PixelLab返修 r16\nP 旧新："+(["A","B","C","D"][pod_variant] if pod_finish_on else "v4旧化基线")+" · K切换差分 · O开关盖\n只替换P12实体表面；玻璃、屏幕、灯管与模型保持。"
