shader_type spatial;
render_mode unshaded, cull_back;

// Runtime-only counterpart to the established paper-hero ribbon-light proxy.
// It intentionally has no emission: the value drops to emergency readability
// when the Room 1 strip-light toggle is off.
uniform vec4 base_tint : source_color = vec4(0.57, 0.65, 0.65, 1.0);
uniform float strip_on = 1.0;

void fragment() {
	float light_level = 0.16 + strip_on * 0.38;
	ALBEDO = base_tint.rgb * light_level;
	ROUGHNESS = 0.95;
	SPECULAR = 0.0;
}
