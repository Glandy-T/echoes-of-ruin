shader_type spatial;
uniform float strip_on = 1.0;
varying vec3 world_position;
varying vec3 world_normal;
void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize(MODEL_NORMAL_MATRIX * NORMAL);
}
void fragment() {
	vec3 base = vec3(0.6, 0.49, 0.34);
	ALBEDO = base;
	ROUGHNESS = 0.9;
	SPECULAR = 0.05;
	float illumination = 0.0;
	for (int i = 0; i < 8; i++) {
		float x = mix(0.205, 20.795, (float(i) + 0.5) / 8.0);
		vec3 front = vec3(x, 3.05, -0.205) - world_position;
		vec3 back = vec3(x, 3.05, -9.295) - world_position;
		illumination += max(dot(normalize(world_normal), normalize(front)), 0.0) / (1.0 + dot(front, front));
		illumination += max(dot(normalize(world_normal), normalize(back)), 0.0) / (1.0 + dot(back, back));
	}
	EMISSION = base * vec3(0.67, 0.8, 0.86) * illumination * 4.0 * strip_on;
}
