shader_type spatial;
render_mode unshaded, cull_back;

// r31 shader-only review of the Room 1 door leaf.  The r30 pixel_map is used
// unchanged; only how it is shown on screen differs from the v3 door shader.
//
// Measured on the r30 same-camera captures (see the r31 README):
//   * v3 darkened the leaf on a long, steady top-to-bottom ramp while the
//     surrounding baked wall stays nearly flat until the floor contact.  On an
//     otherwise clean panel that ramp reads as a sheen on smooth sheet metal.
//   * v3's low multiplier left only ~45% of the wall's local pixel contrast,
//     so the PixelLab coating variation and edge deposits vanished at play
//     distance.
// r31 therefore (1) follows the wall's flat profile and keeps a contact
// darkening near the floor only, and (2) expands pixel contrast around a
// reference colour (see the correction note below).  Hue tint, lighting, UV
// and the emergency-strip coupling are kept from v3.

uniform sampler2D pixel_map : source_color, filter_nearest, repeat_disable;
uniform float strip_on = 1.0;
// Wall-matched brightness of the leaf above the floor-contact zone.
uniform float leaf_level = 0.19;
// Brightness kept at the very bottom edge, relative to leaf_level.  Kept well
// below v4's rejected lift so no light source appears under the door.
uniform float contact_floor = 0.62;
uniform float contact_height = 0.45;
// Pixel-contrast expansion around grain_reference: pixels darker than it use
// grain_contrast, lighter ones grain_light_contrast.
//
// CORRECTION (found while building r32): under this project's gl_compatibility
// renderer the sampled pixel_map values are sRGB-encoded, not linear.  The r31
// default reference below was computed in linear space, so it lies under the
// r30 coat colour: nearly every r30 pixel counts as "lighter" and r31 only
// applied ~1.2x expansion, with leaf_level compensating the brightness.  The
// defaults are kept unchanged so r31 renders exactly as reviewed; pass an
// sRGB-space reference (texture median / 255) for new uses, as r32 does.
uniform float grain_contrast = 2.6;
uniform float grain_light_contrast = 1.2;
uniform vec3 grain_reference = vec3(0.4735, 0.5271, 0.4508);

void fragment() {
	vec4 surface = texture(pixel_map, UV);
	vec3 delta = surface.rgb - grain_reference;
	float lighter = step(0.0, dot(delta, vec3(0.2126, 0.7152, 0.0722)));
	vec3 painted = max(grain_reference + delta * mix(grain_contrast, grain_light_contrast, lighter), vec3(0.0));
	// GLB UV V is downward in Godot: top of the door has UV.y near zero.
	float height_fraction = 1.0 - UV.y;
	float contact = mix(contact_floor, 1.0, smoothstep(0.0, contact_height, height_fraction));
	float base = leaf_level * contact;
	float emergency = mix(0.55, 1.0, strip_on);
	ALBEDO = painted * vec3(0.90, 1.03, 1.04) * base * emergency;
	ROUGHNESS = 0.94;
	SPECULAR = 0.0;
}
