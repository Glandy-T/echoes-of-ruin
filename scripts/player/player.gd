extends CharacterBody2D

const SPEED = 200.0
const JUMP_VELOCITY = -350.0
const GRAVITY = 900.0

@onready var anim = $AnimatedSprite2D

var facing_left = false
var input_locked := false


func set_input_locked(locked: bool) -> void:
	input_locked = locked
	if input_locked:
		velocity.x = 0.0


func _physics_process(delta):
	# 重力
	if not is_on_floor():
		velocity.y += GRAVITY * delta

	if input_locked:
		velocity.x = 0.0
		anim.play("idle")
		anim.flip_h = facing_left
		move_and_slide()
		return

	# 跳跃
	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = JUMP_VELOCITY

	# 左右移动
	var direction = Input.get_axis("move_left", "move_right")

	if direction != 0:
		velocity.x = direction * SPEED
		anim.play("walk")

		if direction < 0:
			facing_left = true
		elif direction > 0:
			facing_left = false
	else:
		velocity.x = 0
		anim.play("idle")

	# 站立和移动都按照最后方向翻转
	anim.flip_h = facing_left

	move_and_slide()
