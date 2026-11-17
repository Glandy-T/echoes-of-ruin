shader_type spatial;
render_mode unshaded, cull_back;

// Status window as dark glass with the lamp behind it (user choice 2026-11-17).
// The whole window carries the state colour, brighter in the middle and
// falling off toward the frame, overall one step darker than a flat fill.
// lamp_color is copied from the door's existing feedback colour every update,
// so the yellow flash / red / green logic is unchanged.

uniform vec3 lamp_color = vec3(0.025, 0.045, 0.05);
uniform vec3 glass_tint = vec3(0.020, 0.032, 0.034);
uniform float glass_transmit = 0.82;
uniform float edge_level = 0.50;
uniform float aspect = 1.8;

void fragment() {
	vec2 p = (UV - 0.5) * vec2(aspect, 1.0) * 2.0;
	float r = length(p) / length(vec2(aspect, 1.0));
	float lamp = mix(1.0, edge_level, smoothstep(0.15, 0.95, r));
	ALBEDO = max(glass_tint, lamp_color * glass_transmit * lamp);
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}
