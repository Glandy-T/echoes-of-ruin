shader_type spatial;

uniform sampler2D screen_pixels : source_color, filter_nearest, repeat_disable;
uniform float core_energy = 2.0;
uniform float powered = 1.0;

void fragment() {
	vec3 pixels = texture(screen_pixels, UV).rgb;
	float brightness = max(pixels.r, max(pixels.g, pixels.b));
	float glyphs = smoothstep(0.28, 0.52, brightness);
	float content = smoothstep(0.045, 0.085, UV.x)
		* (1.0 - smoothstep(0.86, 0.93, UV.x))
		* smoothstep(0.15, 0.205, UV.y)
		* (1.0 - smoothstep(0.83, 0.89, UV.y));
	vec3 red_pixels = vec3(1.0, 0.075, 0.025) * brightness;
	ALBEDO = red_pixels * mix(0.12, mix(0.3, 1.0, glyphs), powered);
	ROUGHNESS = 0.8;
	SPECULAR = 0.0;
	EMISSION = red_pixels * core_energy * glyphs * content * powered;
}
