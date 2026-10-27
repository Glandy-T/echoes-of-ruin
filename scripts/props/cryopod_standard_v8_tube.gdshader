shader_type spatial;
uniform float tube_powered = 1.0;
void fragment() {
	ALBEDO = vec3(0.15, 0.22, 0.24);
	ROUGHNESS = 0.86;
	SPECULAR = 0.0;
	EMISSION = vec3(0.58, 0.76, 0.80) * 0.65 * tube_powered;
}
