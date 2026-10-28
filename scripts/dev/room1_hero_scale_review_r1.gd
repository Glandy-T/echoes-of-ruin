extends "res://scripts/dev/room1_dialogue_adapter_review_r1.gd"

const ORIGINAL_HEIGHT := 1.65
const CANDIDATE_HEIGHT := 1.4025
const DIGITS := ["111101101101111", "010110010010111", "111001111100111", "111001111001111", "101101111001001", "111100111001111", "111100111101111", "111001001001001", "111101111101111", "111101111001111"]
var smaller_hero := true

func _ready() -> void:
	super._ready()
	if not Engine.is_editor_hint():
		apply_hero_size()
		apply_pod_numbers()

func apply_pod_numbers() -> void:
	for n in range(1, 21):
		if n == 12:
			continue # P12 uses the newer v8 asset, already labelled 12.
		var pod := $Pods.get_node("P%02d" % n)
		for specification in [["pod_v3_shell_end", Vector2i(58, 38), 2], ["pod_v3_lid", Vector2i(69, 199), 1]]:
			var mesh := pod.find_child(specification[0], true, false) as MeshInstance3D
			if not mesh:
				push_error("Missing numbered surface for P%02d: %s" % [n, specification[0]])
				continue
			var material := mesh.get_active_material(0).duplicate() as ShaderMaterial
			var original := material.get_shader_parameter("color_map") as Texture2D
			var img := original.get_image().duplicate() as Image
			var start: Vector2i = specification[1]
			var scale: int = specification[2]
			var ink := img.get_pixel(start.x, start.y)
			var background := img.get_pixel(start.x - 2, start.y + scale)
			for y in range(5 * scale):
				for x in range(7 * scale):
					img.set_pixel(start.x + x, start.y + y, background)
			for digit_index in 2:
				var digit := n / 10 if digit_index == 0 else n % 10
				var pattern: String = DIGITS[digit]
				for y in 5:
					for x in 3:
						if pattern[y * 3 + x] == "1":
							for dy in scale:
								for dx in scale:
									img.set_pixel(start.x + (digit_index * 4 + x) * scale + dx, start.y + y * scale + dy, ink)
			material.set_shader_parameter("color_map", ImageTexture.create_from_image(img))
			mesh.set_surface_override_material(0, material)

func apply_hero_size() -> void:
	var height := CANDIDATE_HEIGHT if smaller_hero else ORIGINAL_HEIGHT
	for sprite: Sprite3D in [paper_hero, bloom_paper_hero]:
		sprite.pixel_size = height / float(VISIBLE_HEIGHT_PX)
		sprite.position.y = (float(FOOT_ROW_PX) - float(FRAME_HEIGHT) * 0.5) * sprite.pixel_size
	_sync_paper_hero()
	_update_info()

func _unhandled_key_input(event: InputEvent) -> void:
	if review_ui and review_ui.is_modal_open():
		return
	if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_Y:
		smaller_hero = not smaller_hero
		apply_hero_size()
		get_viewport().set_input_as_handled()
		return
	super._unhandled_key_input(event)

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 主角比例对照 r1\nY切换原尺寸／缩小15%% · WASD移动 · E调查 · Enter翻页\n当前：%s；仅调整纸片画面，碰撞和阴影仍沿用原测试体。" % ("缩小15%" if smaller_hero else "原尺寸")
