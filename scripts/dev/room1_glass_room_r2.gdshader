shader_type spatial;
render_mode blend_mix, cull_back;

uniform sampler2D pixel_reflections : source_color, filter_nearest, repeat_disable;
uniform float reflection_strength = 1.0;
uniform vec3 glass_tint : source_color = vec3(0.2, 0.35, 0.4);

void fragment() {
	vec3 pixels = texture(pixel_reflections, UV).rgb;
	float reflection = smoothstep(0.08, 0.25, max(pixels.r, max(pixels.g, pixels.b))) * reflection_strength;
	ALBEDO = mix(glass_tint, pixels, reflection);
	ALPHA = mix(0.14, 0.68, reflection);
	ROUGHNESS = 0.32;
	SPECULAR = 0.08;
	// Reflections now receive room lighting instead of adding light in darkness.
	EMISSION = vec3(0.0);
}
