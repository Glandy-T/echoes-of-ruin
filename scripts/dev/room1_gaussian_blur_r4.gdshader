shader_type canvas_item;
render_mode unshaded;

uniform vec2 direction = vec2(1.0, 0.0);
uniform float sigma = 7.0;

void fragment() {
	vec3 sum = vec3(0.0);
	float weights = 0.0;
	for (int i = -21; i <= 21; i++) {
		float offset = float(i);
		float weight = exp(-0.5 * offset * offset / (sigma * sigma));
		sum += texture(TEXTURE, UV + direction * TEXTURE_PIXEL_SIZE * offset).rgb * weight;
		weights += weight;
	}
	COLOR = vec4(sum / weights, 1.0);
}
