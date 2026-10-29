shader_type spatial;
render_mode unshaded, cull_disabled;
uniform vec3 tint_color : source_color = vec3(0.110, 0.140, 0.130);

varying float world_height;

void vertex() {
    world_height = (MODEL_MATRIX * vec4(VERTEX, 1.0)).y;
}

void fragment() {
    // An unpowered diffuser is a physical trim, not an emissive strip. Follow
    // the same steep falloff as the adjacent emergency-lit rear wall.
    float normalized_height = clamp(world_height / 2.4, 0.0, 1.0);
    float room_falloff = mix(0.30, 1.0, smoothstep(0.0, 0.38, normalized_height));
    ALBEDO = tint_color * room_falloff;
    ROUGHNESS = 1.0;
    SPECULAR = 0.0;
}
