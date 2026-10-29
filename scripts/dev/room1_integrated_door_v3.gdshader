shader_type spatial;
render_mode unshaded, cull_back;

uniform sampler2D pixel_map : source_color, filter_nearest, repeat_disable;
uniform float strip_on = 1.0;

void fragment() {
    vec4 surface = texture(pixel_map, UV);
    // Match Room 1's baked rear-wall falloff at the same screen height.
    // The interactive window and jamb pixels are separate runtime materials.
    // GLB UV V is downward in Godot: top of the door has UV.y near zero.
    float height_fraction = 1.0 - UV.y;
    float base = mix(0.085, 0.095, smoothstep(0.0, 0.14, height_fraction));
    base += 0.048 * smoothstep(0.14, 0.25, height_fraction);
    base += 0.055 * smoothstep(0.25, 1.0, height_fraction);
    float emergency = mix(0.55, 1.0, strip_on);
    ALBEDO = surface.rgb * vec3(0.90, 1.03, 1.04) * base * emergency;
    ROUGHNESS = 0.94;
    SPECULAR = 0.0;
}
