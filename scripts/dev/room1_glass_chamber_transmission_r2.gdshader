shader_type spatial;
render_mode blend_mix, cull_back;

uniform sampler2D pixel_reflections : source_color, filter_nearest, repeat_disable;
uniform float reflection_strength = 1.0;
uniform vec3 glass_tint : source_color = vec3(0.2, 0.35, 0.4);

uniform float chamber_powered = 0.0;
uniform vec3 chamber_light_position;
varying vec3 world_position;
void vertex() { world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment() {
	vec3 pixels = texture(pixel_reflections, UV).rgb;
	float reflection = smoothstep(0.08, 0.25, max(pixels.r, max(pixels.g, pixels.b))) * reflection_strength;
	ALBEDO = mix(glass_tint, pixels, reflection);
	ALPHA = mix(0.14, 0.68, reflection);
	ROUGHNESS = 0.32;
	SPECULAR = 0.08;
	// Approximate transmitted chamber radiance; switch follows the actual interior light.
	float glow = exp(-dot(world_position - chamber_light_position, world_position - chamber_light_position) / 0.22);
	EMISSION = vec3(0.12, 0.46, 0.56) * glow * (1.0 - reflection * 0.5) * 1.3 * chamber_powered;
}
