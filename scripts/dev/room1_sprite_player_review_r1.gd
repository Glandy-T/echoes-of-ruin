@tool
extends "res://scripts/dev/room1_pod_standard_v8_review.gd"

## Review-only paper character: it keeps the existing 1.65 m CharacterBody3D
## for movement, collision and contact shadow, replacing only its visible capsule.
const IDLE_SHEET := preload("res://assets/characters/idle.png")
const WALK_SHEET := preload("res://assets/characters/walk.png")
const FRAME_WIDTH := 96
const FRAME_HEIGHT := 128
const VISIBLE_HEIGHT_PX := 96
const CHARACTER_HEIGHT_M := 1.65
const FOOT_ROW_PX := 120
const FRAME_RATE := 5.0

var paper_hero: Sprite3D
var bloom_paper_hero: Sprite3D
var paper_time := 0.0
var paper_walking := false
var paper_facing_left := false

func _ready() -> void:
	super._ready()
	if Engine.is_editor_hint() or not player:
		return
	# Keep the capsule logically visible so ancestor contact-shadow code remains on,
	# but remove it from both cameras' visible layer.
	actor_mesh.layers = 0
	paper_hero = _make_paper_sprite()
	player.add_child(paper_hero)
	bloom_paper_hero = _make_paper_sprite()
	bloom_paper_hero.modulate = Color(0, 0, 0, 1)
	bloom_paper_hero.no_depth_test = false
	bloom_camera.get_parent().add_child(bloom_paper_hero)
	_sync_paper_hero()
	_update_info()

func _make_paper_sprite() -> Sprite3D:
	var sprite := Sprite3D.new()
	sprite.texture = IDLE_SHEET
	sprite.hframes = 4
	sprite.vframes = 1
	sprite.frame = 0
	sprite.pixel_size = CHARACTER_HEIGHT_M / float(VISIBLE_HEIGHT_PX)
	# Alpha reaches row 120 in every legacy frame. This puts the visible feet at
	# player y=0 while preserving the original image aspect ratio.
	sprite.position.y = (float(FOOT_ROW_PX) - float(FRAME_HEIGHT) * 0.5) * sprite.pixel_size
	sprite.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	sprite.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return sprite

func _process(delta: float) -> void:
	super._process(delta)
	if not is_instance_valid(paper_hero):
		return
	var horizontal_speed := Vector2(player.velocity.x, player.velocity.z).length()
	var next_walking := horizontal_speed > 0.03
	if absf(player.velocity.x) > 0.03:
		paper_facing_left = player.velocity.x < 0.0
	if next_walking != paper_walking:
		paper_walking = next_walking
		paper_time = 0.0
		paper_hero.texture = WALK_SHEET if paper_walking else IDLE_SHEET
		paper_hero.hframes = 6 if paper_walking else 4
		bloom_paper_hero.texture = paper_hero.texture
		bloom_paper_hero.hframes = paper_hero.hframes
	paper_time += delta
	var count := 6 if paper_walking else 4
	var frame := int(floor(paper_time * FRAME_RATE)) % count
	paper_hero.frame = frame
	paper_hero.flip_h = paper_facing_left
	_sync_paper_hero()

func _sync_paper_hero() -> void:
	if not is_instance_valid(paper_hero):
		return
	bloom_paper_hero.global_transform = paper_hero.global_transform
	bloom_paper_hero.frame = paper_hero.frame
	bloom_paper_hero.flip_h = paper_hero.flip_h
	bloom_paper_hero.visible = paper_hero.visible

func _update_info() -> void:
	if info:
		info.text = "Room 1 / 2D纸片主角 r1 · 待审\nWASD移动 · R复位 · O开/关盖 · G内侧灯管 · B屏幕 · L墙灯\n旧idle/walk精灵以1.65m身高嵌入3D空间；碰撞与接触阴影仍使用胶囊体。"
