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
uniform float baked_energy = 1.2;
uniform vec3 actor_feet = vec3(10.5, 0.0, -4.75);
uniform float actor_shadow_enabled = 1.0;
uniform vec3 capsule_a;
uniform vec3 capsule_b;
varying vec3 world_position;
varying vec3 world_normal;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	world_normal = normalize(MODEL_NORMAL_MATRIX * NORMAL);
}

float capsule_visibility(vec3 origin, vec3 destination) {
	vec3 a = capsule_a;
	vec3 b = capsule_b;
	vec3 d1 = destination - origin;
	vec3 d2 = b - a;
	vec3 r = origin - a;
	float aa = dot(d1, d1);
	float ee = dot(d2, d2);
	float ff = dot(d2, r);
	float cc = dot(d1, r);
	float bb = dot(d1, d2);
	float denominator = max(aa * ee - bb * bb, 0.000001);
	float s = clamp((bb * ff - cc * ee) / denominator, 0.0, 1.0);
	float t = (bb * s + ff) / ee;
	if (t < 0.0) {
		t = 0.0;
		s = clamp(-cc / aa, 0.0, 1.0);
	} else if (t > 1.0) {
		t = 1.0;
		s = clamp((bb - cc) / aa, 0.0, 1.0);
	}
	float separation = length(origin + d1 * s - a - d2 * t);
	return smoothstep(0.19, 0.25, separation);
}

void ribbon_sample(vec3 light_position, vec3 emitter_normal, inout float visible_weight, inout float weight_sum) {
	vec3 ray = light_position - world_position;
	float distance_squared = max(dot(ray, ray), 0.01);
	vec3 direction = ray / sqrt(distance_squared);
	float facing = max(dot(normalize(world_normal), direction), 0.0);
	float emitting = abs(dot(emitter_normal, -direction));
	float weight = facing * emitting / distance_squared;
	visible_weight += weight * capsule_visibility(world_position + normalize(world_normal) * 0.004, light_position);
	weight_sum += weight;
}

float actor_visibility() {
	// Limit fragment work to surfaces close enough to show a meaningful shadow.
	if (actor_shadow_enabled < 0.5 || distance(world_position.xz, actor_feet.xz) > 6.0 || world_position.y > actor_feet.y + 1.7) {
		return 1.0;
	}
	float visible_weight = 0.0;
	float weight_sum = 0.0;
	for (int i = 0; i < 16; i++) {
		float u = (float(i) + 0.5) / 16.0;
		float x = mix(0.205, 20.795, u);
		float z = mix(-0.205, -9.295, u);
		ribbon_sample(vec3(x, 3.05, -0.205), vec3(0.0, 0.0, -1.0), visible_weight, weight_sum);
		ribbon_sample(vec3(x, 3.05, -9.295), vec3(0.0, 0.0, 1.0), visible_weight, weight_sum);
		// Shorter side ribbons contribute proportionately to their emitting area.
		float saved_visible = visible_weight;
		float saved_sum = weight_sum;
		ribbon_sample(vec3(0.205, 3.05, z), vec3(1.0, 0.0, 0.0), visible_weight, weight_sum);
		ribbon_sample(vec3(20.795, 3.05, z), vec3(-1.0, 0.0, 0.0), visible_weight, weight_sum);
		visible_weight = saved_visible + (visible_weight - saved_visible) * 0.441;
		weight_sum = saved_sum + (weight_sum - saved_sum) * 0.441;
	}
	float visibility = visible_weight / max(weight_sum, 0.000001);
	// Keep part of the baked indirect bounce instead of cutting it to black.
	return mix(0.18, 1.0, visibility);
}

// Full-room candidate: native pixel maps repeat by reflection, without tile gaps.
uniform sampler2D floor_material_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D wall_material_map : source_color, filter_nearest, repeat_disable;
uniform float full_surface_enabled = 1.0;
uniform int full_surface_kind = 0;
uniform float material_tile_m = 3.2;
uniform vec4 material_center : source_color = vec4(1.0);
uniform float material_strength = 1.0;
vec2 mirrored_uv(vec2 value) {
    return vec2(1.0) - abs(mod(value, vec2(2.0)) - vec2(1.0));
}
float mirrored_u(float value) {
    return 1.0 - abs(mod(value, 2.0) - 1.0);
}
void fragment() {
	vec3 color = texture(color_map, UV).rgb * base_color.rgb;
    if (full_surface_enabled > 0.5) {
        if (full_surface_kind == 1 && world_normal.y > 0.9) {
            vec2 coord = (world_position.xz - vec2(0.2,-9.3)) / material_tile_m;
            color = mix(material_center.rgb, texture(floor_material_map, mirrored_uv(coord)).rgb, material_strength) * base_color.rgb;
            // Only the actual room perimeter receives the faint edge finish.
            float edge = min(min(world_position.x-0.2,20.8-world_position.x), min(world_position.z+9.3,-0.2-world_position.z));
            float darken = edge < 0.075 ? 0.96 : (edge < 0.15 ? 0.98 : 1.0);
            color *= darken;
        } else if (full_surface_kind == 2 && abs(world_normal.y) < 0.1) {
            float along = abs(world_normal.x) > 0.9 ? -world_position.z-0.2 : world_position.x-0.2;
            vec2 coord = vec2(mirrored_u(along/material_tile_m),1.0-world_position.y/3.4);
            // Keep the approved lamp housing, diffuser and base protection band.
            if (world_position.y > 0.325 && world_position.y < 2.875) {
                float corner_distance = abs(world_normal.x) > 0.9
                    ? min(world_position.z+9.3, -0.2-world_position.z)
                    : min(world_position.x-0.2, 20.8-world_position.x);
                float corner = clamp((0.65-corner_distance)/0.65,0.0,1.0);
                float foot = clamp((0.85-world_position.y)/0.525,0.0,1.0);
                float doorway = 0.0;
                if (world_normal.z > 0.9) {
                    float jamb_distance = min(abs(world_position.x-9.8),abs(world_position.x-11.2));
                    doorway = clamp((0.25-jamb_distance)/0.25,0.0,1.0) * step(world_position.y,2.5);
                    if (world_position.x >= 9.8 && world_position.x <= 11.2) {
                        doorway = max(doorway,clamp((0.18-(world_position.y-2.4))/0.18,0.0,1.0));
                    }
                }
                float feature = floor(max(max(corner,foot),doorway)*3.0+0.001)/3.0;
                vec3 sample_color = texture(wall_material_map,coord).rgb * base_color.rgb;
                // Preserve the quiet non-repeating room-sized base. The small-map
                // clusters are only a faint material finish near real intersections.
                color = mix(color,sample_color,material_strength*(0.08+0.42*feature));
                color *= 1.0-0.015*feature;
            }
        }
    }

	ALBEDO = color;
	ROUGHNESS = 0.95;
	SPECULAR = 0.08;
	EMISSION = color * texture(strip_irradiance, UV2).rgb * baked_energy * actor_visibility();
	vec3 diffuser = texture(emission_map, UV).rgb * has_emission_map;
	float diffuser_mask = uniform_strip_emission * step(0.00001, max(diffuser.r, max(diffuser.g, diffuser.b)));
	EMISSION *= 1.0 - diffuser_mask;
	EMISSION += diffuser * strip_surface_energy * mix(1.0, diffuser_radiance_scale, uniform_strip_emission);
}
