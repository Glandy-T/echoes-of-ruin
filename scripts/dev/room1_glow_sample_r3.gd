@tool
extends "res://scripts/dev/room1_glow_sample_r2.gd"

var content_emission_on := true
var gentler_spill_on := true

func _ready() -> void:
	super._ready()
	apply_sample_state()

func apply_sample_state() -> void:
	super.apply_sample_state()
	if soft_screen:
		soft_screen.shader = preload("res://scripts/dev/room1_screen_content_emission_r3.gdshader") if content_emission_on else preload("res://scripts/dev/room1_screen_soft_emission.gdshader")
	if sample_ready:
		screen_proxies["P12"].light_energy = 0.004 if gentler_spill_on else 0.012
		screen_proxies["P12"].omni_range = 0.65 if gentler_spill_on else 0.5
		screen_proxies["P12"].omni_attenuation = 1.5 if gentler_spill_on else 2.5
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	super._unhandled_key_input(event)
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.physical_keycode:
		KEY_C: content_emission_on = not content_emission_on
		KEY_J: gentler_spill_on = not gentler_spill_on
	apply_sample_state()

func _update_info() -> void:
	if info:
		info.text = "荧光小样 r3 / 内容发光、减弱描边 · 待审\n1屏幕 2舱窗 3整舱 4室内\nC内容发光 %s · J柔和投光 %s · N光晕 %s · P附近投光\nV像素反光 · B屏幕 · G窗光 · H说明。玻璃接缝留待后续。" % [content_emission_on, gentler_spill_on, halo_on]
