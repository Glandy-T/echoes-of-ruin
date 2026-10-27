shader_type spatial;
render_mode blend_mix, depth_prepass_alpha, cull_disabled, unshaded;

// A controllable approximation for the dynamic Sprite3D. Room surfaces use a
// baked lightmap, which cannot light this camera-facing plane directly.
uniform sampler2D paper_texture : source_color, filter_nearest, repeat_disable;
uniform float strip_on = 1.0;

varying vec3 paper_world_position;

void vertex() {
	paper_world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec4 pixel = texture(paper_texture, UV);
	float ribbon = 0.0;
	for (int i = 0; i < 8; i++) {
		float x = mix(0.205, 20.795, (float(i) + 0.5) / 8.0);
		vec3 front = vec3(x, 3.05, -0.205) - paper_world_position;
		vec3 rear = vec3(x, 3.05, -9.295) - paper_world_position;
		ribbon += 1.0 / (1.0 + 0.18 * dot(front, front));
		ribbon += 1.0 / (1.0 + 0.18 * dot(rear, rear));
	}
	// The off-state remains faintly readable through ambient emergency light.
	// The on-state uses the same continuous-ribbon positions as the room shader.
	// Sixteen finite-distance terms exceed 1.0 near the room centre. Normalize
	// before clamping so movement through the aisle still changes the response.
	float light_level = 0.10 + strip_on * (0.13 + 0.38 * clamp(ribbon * 0.5, 0.0, 1.0));
	vec3 cool_light = vec3(0.78, 0.91, 1.0) * light_level;
	ALBEDO = pixel.rgb * cool_light;
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
	ALPHA = pixel.a;
}
