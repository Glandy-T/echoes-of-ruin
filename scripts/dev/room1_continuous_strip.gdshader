shader_type spatial;
render_mode diffuse_burley;

uniform sampler2D color_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D emission_map : source_color, filter_nearest, repeat_disable;
uniform vec4 base_color : source_color = vec4(1.0);
uniform vec3 uv_offset = vec3(0.0);
uniform float strip_surface_energy = 0.12;
uniform float strip_light_energy = 0.24;
uniform float has_emission_map = 0.0;
varying vec3 world_position;
varying vec3 world_normal;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize(MODEL_NORMAL_MATRIX * NORMAL);
}

float line_light(vec3 a, vec3 b) {
	vec3 ab = b - a;
	float t = clamp(dot(world_position - a, ab) / dot(ab, ab), 0.0, 1.0);
	vec3 to_light = a + t * ab - world_position;
	float distance_squared = dot(to_light, to_light);
	float facing = max(dot(normalize(world_normal), normalize(to_light)), 0.2);
	return facing / (1.0 + distance_squared * 0.3);
}

void fragment() {
	vec2 uv = UV + uv_offset.xy;
	vec3 color = texture(color_map, uv).rgb * base_color.rgb;
	ALBEDO = color;
	ROUGHNESS = 0.95;
	SPECULAR = 0.08;
	// Four continuous perimeter segments: a stylized fill approximation, not GI.
	float illumination = line_light(vec3(0.4, 3.05, -0.4), vec3(20.6, 3.05, -0.4));
	illumination += line_light(vec3(0.4, 3.05, -9.1), vec3(20.6, 3.05, -9.1));
	illumination += line_light(vec3(0.4, 3.05, -0.4), vec3(0.4, 3.05, -9.1));
	illumination += line_light(vec3(20.6, 3.05, -0.4), vec3(20.6, 3.05, -9.1));
	EMISSION = color * vec3(0.82, 0.9, 0.95) * illumination * strip_light_energy;
	EMISSION += texture(emission_map, uv).rgb * has_emission_map * strip_surface_energy;
}
