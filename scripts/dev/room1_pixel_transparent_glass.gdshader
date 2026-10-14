shader_type spatial;
render_mode blend_mix, cull_back;

uniform sampler2D pixel_reflections : source_color, filter_nearest, repeat_disable;
uniform float reflection_strength = 1.0;
uniform vec3 glass_tint : source_color = vec3(0.2, 0.35, 0.4);

void fragment() {
	vec3 pixels = texture(pixel_reflections, UV).rgb;
	float brightness = max(pixels.r, max(pixels.g, pixels.b));
	// Keep the bright pixel marks; the flat painted glass color becomes transparent.
	float reflection = smoothstep(0.08, 0.25, brightness) * reflection_strength;
	ALBEDO = mix(glass_tint, pixels, reflection);
	ALPHA = mix(0.14, 0.68, reflection);
	ROUGHNESS = 0.32;
	SPECULAR = 0.08;
	EMISSION = pixels * reflection * 0.16;
}
