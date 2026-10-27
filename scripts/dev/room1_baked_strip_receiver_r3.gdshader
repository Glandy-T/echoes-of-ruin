shader_type spatial;
uniform sampler2D color_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D emission_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D strip_irradiance : filter_linear, repeat_disable;
uniform vec4 base_color : source_color = vec4(1.0);
uniform float has_emission_map = 0.0;
// Self-emitting diffuser pixels must not be brightened differently per UV2 chart.
uniform float uniform_strip_emission = 0.0;
uniform float diffuser_radiance_scale = 1.0;
uniform float strip_surface_energy = 0.7;
uniform float baked_energy = 0.45;

void fragment() {
	vec3 color = texture(color_map, UV).rgb * base_color.rgb;
	ALBEDO = color;
	ROUGHNESS = 0.95;
	SPECULAR = 0.08;
	// Continuous emitting-surface irradiance already includes static occlusion.
	EMISSION = color * texture(strip_irradiance, UV2).rgb * baked_energy;
	vec3 diffuser = texture(emission_map, UV).rgb * has_emission_map;
	float diffuser_mask = uniform_strip_emission * step(0.00001, max(diffuser.r, max(diffuser.g, diffuser.b)));
	EMISSION *= 1.0 - diffuser_mask;
	EMISSION += diffuser * strip_surface_energy * mix(1.0, diffuser_radiance_scale, uniform_strip_emission);
}
