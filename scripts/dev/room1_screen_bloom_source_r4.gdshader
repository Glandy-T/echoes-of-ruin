shader_type spatial;
render_mode unshaded;

uniform sampler2D screen_pixels : source_color, filter_nearest, repeat_disable;
uniform float powered = 1.0;

void fragment() {
	vec3 pixels = texture(screen_pixels, UV).rgb;
	float brightness = max(pixels.r, max(pixels.g, pixels.b));
	float glyphs = smoothstep(0.28, 0.52, brightness);
	float content = smoothstep(0.045, 0.085, UV.x)
		* (1.0 - smoothstep(0.86, 0.93, UV.x))
		* smoothstep(0.15, 0.205, UV.y)
		* (1.0 - smoothstep(0.83, 0.89, UV.y));
	ALBEDO = pixels * vec3(0.75, 0.95, 1.0) * glyphs * content * powered;
}
