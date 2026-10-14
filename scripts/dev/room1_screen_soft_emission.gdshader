shader_type spatial;

uniform sampler2D screen_pixels : source_color, filter_nearest, repeat_disable;
uniform float core_energy = 2.0;
uniform float powered = 1.0;

void fragment() {
	vec3 pixels = texture(screen_pixels, UV).rgb;
	float brightness = max(pixels.r, max(pixels.g, pixels.b));
	float glyphs = smoothstep(0.06, 0.2, brightness);
	float edge = min(min(UV.x, 1.0 - UV.x), min(UV.y, 1.0 - UV.y));
	float soft_edge = smoothstep(0.03, 0.14, edge);
	ALBEDO = pixels * mix(0.12, 1.0, powered);
	ROUGHNESS = 0.8;
	SPECULAR = 0.0;
	// Text/bars are the primary emitters. The outside frame no longer emits equally.
	EMISSION = pixels * vec3(0.75, 0.95, 1.0) * core_energy * glyphs * soft_edge * powered;
}
