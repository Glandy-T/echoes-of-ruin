shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never;

// Door light direction B (2026-11-17): the slot lamps sit deep in the jamb,
// so what reads from the room is the light they throw on the reveal, not the
// lamp itself.  Additive wash over the existing baked surfaces; no texture,
// no grime, no new geometry other than these thin overlay faces.
// Vertices are in the stationary door root (same frame as r17's phosphor).

uniform vec3 wash_color : source_color = vec3(0.30, 0.66, 0.42);
uniform float wash_energy = 0.40;
uniform float passage_power = 0.0;
// Slot depth (root-local z) and how fast the light fades toward the room.
uniform float slot_z = -0.060;
uniform float reveal_decay = 0.09;
uniform float floor_decay = 0.20;
// 0 = side reveal, 1 = header underside, 2 = floor threshold.
uniform int face_kind = 0;
uniform float leaf_min_x = -0.695;
uniform float leaf_max_x = 0.695;
varying vec3 local_pos;

void vertex() {
	local_pos = VERTEX;
}

void fragment() {
	float toward_room = max(local_pos.z - slot_z, 0.0);
	float decay = face_kind == 2 ? floor_decay : reveal_decay;
	float light = exp(-toward_room / decay);
	float side_exposed = 1.0;
	if (face_kind == 0) {
		// A side slot only lights its reveal once the leaf has cleared it.
		side_exposed = (local_pos.x < leaf_min_x || local_pos.x > leaf_max_x) ? 1.0 : 0.0;
		light *= mix(0.55, 1.0, smoothstep(-1.2, -0.3, local_pos.y));
	} else if (face_kind == 1) {
		light *= 0.75;
	} else {
		// Threshold is lit mostly near the two vertical slots.
		float edge = exp(-(0.70 - abs(local_pos.x)) / 0.22);
		light *= 0.55 * mix(0.35, 1.0, edge);
	}
	ALBEDO = wash_color * wash_energy * light * passage_power * side_exposed;
}
