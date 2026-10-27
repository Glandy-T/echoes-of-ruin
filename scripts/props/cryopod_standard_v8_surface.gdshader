shader_type spatial;

// Per-instance receiver.  The two pose maps are deliberately blended only for
// the P12 review placement; a room may replace them through the controller.
uniform sampler2D color_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D closed_irradiance : filter_linear, repeat_disable;
uniform sampler2D open_irradiance : filter_linear, repeat_disable;
uniform vec4 base_color : source_color = vec4(1.0);
uniform float baked_energy = 1.2;
uniform float has_baked_maps = 0.0;
uniform float pose_blend = 0.0;
uniform float tube_powered = 1.0;
uniform float tube_flux = 0.60;
uniform float receive_tubes = 0.0;
uniform mat4 chamber_from_world;
uniform vec3 actor_feet = vec3(999.0);
uniform vec3 capsule_a = vec3(999.0);
uniform vec3 capsule_b = vec3(999.0);
uniform float actor_shadow_enabled = 0.0;

varying vec3 world_position;
varying vec3 world_normal;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize(MODEL_NORMAL_MATRIX * NORMAL);
}

float capsule_visibility(vec3 origin, vec3 destination) {
	if (actor_shadow_enabled < 0.5) return 1.0;
	vec3 d1 = destination - origin;
	vec3 d2 = capsule_b - capsule_a;
	vec3 r = origin - capsule_a;
	float aa = dot(d1,d1);
	float ee = dot(d2,d2);
	float ff = dot(d2,r);
	float cc = dot(d1,r);
	float bb = dot(d1,d2);
	float denominator = max(aa * ee - bb * bb, 0.000001);
	float s = clamp((bb * ff - cc * ee) / denominator, 0.0, 1.0);
	float t = (bb * s + ff) / ee;
	if (t < 0.0) { t = 0.0; s = clamp(-cc / aa, 0.0, 1.0); }
	else if (t > 1.0) { t = 1.0; s = clamp((bb - cc) / aa, 0.0, 1.0); }
	float separation = length(origin + d1 * s - capsule_a - d2 * t);
	return smoothstep(0.19, 0.25, separation);
}

void fragment() {
	vec3 color = texture(color_map, UV).rgb * base_color.rgb;
	ALBEDO = color;
	ROUGHNESS = 0.92;
	SPECULAR = 0.08;
	vec3 baked = mix(texture(closed_irradiance, UV2).rgb, texture(open_irradiance, UV2).rgb, pose_blend);
	EMISSION = color * baked * baked_energy * has_baked_maps;

	// The approved v7 interior illumination is two actual 1.70m side tubes,
	// integrated as short strips.  There is intentionally no head-centred light.
	vec3 p = (chamber_from_world * vec4(world_position, 1.0)).xyz;
	vec3 n = normalize(mat3(chamber_from_world) * world_normal);
	float irradiance = 0.0;
	for (int side = 0; side < 2; side++) {
		float s = side == 0 ? -1.0 : 1.0;
		vec3 emit_normal = normalize(vec3(-s, -0.5, 0.0));
		for (int i = 0; i < 12; i++) {
			float z = mix(-0.85, 0.85, (float(i) + 0.5) / 12.0);
			vec3 delta = vec3(s * 0.447, 0.31, z) - p;
			float d = length(delta);
			vec3 ray = delta / max(d, 0.001);
			float receive = max(dot(n, ray), 0.0);
			float emit = max(dot(emit_normal, -ray), 0.0);
			float range_mask = 1.0 - smoothstep(0.75, 1.15, d);
			vec3 source_world = (inverse(chamber_from_world) * vec4(vec3(s * 0.447, 0.31, z), 1.0)).xyz;
			irradiance += receive * emit * range_mask * capsule_visibility(world_position + normalize(world_normal) * 0.004, source_world) * (1.70 / 12.0) / (dot(delta, delta) + 0.01);
		}
	}
	float soft_irradiance = irradiance / (1.0 + 0.65 * irradiance);
	EMISSION += color * vec3(0.60, 0.78, 0.82) * soft_irradiance * tube_flux * tube_powered * receive_tubes;
}
