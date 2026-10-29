shader_type spatial;
render_mode unshaded, cull_back;

uniform sampler2D pixel_map : source_color, filter_nearest, repeat_disable;
uniform float strip_on = 1.0;

void fragment() {
    vec4 surface = texture(pixel_map, UV);
    float height_fraction = 1.0 - UV.y;
    // Reuse v3's wall-family pixel colors. Lift the full leaf only one value
    // step and prevent the contact shadow from collapsing into a black strip.
    float base = mix(0.085, 0.095, smoothstep(0.0, 0.14, height_fraction));
    base += 0.048 * smoothstep(0.14, 0.25, height_fraction);
    base += 0.055 * smoothstep(0.25, 1.0, height_fraction);
    base += 0.125 * (1.0 - smoothstep(0.0, 0.12, height_fraction));
    float emergency = mix(0.55, 1.0, strip_on);
    ALBEDO = surface.rgb * vec3(1.00, 1.15, 1.14) * base * emergency;
    ROUGHNESS = 0.94;
    SPECULAR = 0.0;
}
