shader_type spatial;
render_mode unshaded, cull_back;

// Status window as dark glass with the lamp behind it (user choice 2026-11-17).
// The whole window carries the state colour, brighter in the middle and
// falling off toward the frame, overall one step darker than a flat fill.
// lamp_color is copied from the door's existing feedback colour every update,
// so the yellow flash / red / green logic is unchanged.
//
// Revision (user, same day): the falloff is stepped, not smooth, so it matches
// the pixel art.  The window is evaluated on its own native pixel grid
// (11 x 6 px of the door texture) and each cell takes one of three levels.

uniform vec3 lamp_color = vec3(0.025, 0.045, 0.05);
uniform vec3 glass_tint = vec3(0.020, 0.032, 0.034);
uniform float glass_transmit = 0.82;
uniform vec2 pixel_grid = vec2(11.0, 6.0);
uniform vec3 levels = vec3(1.0, 0.74, 0.50); // centre, middle ring, edge ring

void fragment() {
	vec2 cell = (floor(UV * pixel_grid) + 0.5) / pixel_grid;
	vec2 p = (cell - 0.5) * pixel_grid;        // in native pixels from centre
	vec2 half_size = pixel_grid * 0.5;
	// Normalised "ring" distance: 1.0 on the outermost cells.
	float ring = max(abs(p.x) / (half_size.x - 0.5), abs(p.y) / (half_size.y - 0.5));
	float lamp = ring < 0.45 ? levels.x : (ring < 0.95 ? levels.y : levels.z);
	ALBEDO = max(glass_tint, lamp_color * glass_transmit * lamp);
	ROUGHNESS = 1.0;
	SPECULAR = 0.0;
}
