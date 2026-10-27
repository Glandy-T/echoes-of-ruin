shader_type spatial;
render_mode blend_mix, cull_back;
uniform sampler2D glass_pixels : source_color, filter_nearest, repeat_disable;
uniform float reflections_enabled = 1.0;
uniform float base_opacity = 0.10;
uniform float glass_visible = 1.0;
void fragment() {
	vec4 pixel = texture(glass_pixels, UV);
	float mark = clamp((pixel.a - 24.0 / 255.0) / (80.0 / 255.0), 0.0, 1.0) * reflections_enabled;
	float edge = pow(1.0 - clamp(abs(dot(normalize(NORMAL), normalize(VIEW))), 0.0, 1.0), 3.0);
	ALBEDO = mix(vec3(0.13, 0.21, 0.25), pixel.rgb, mark * 0.75);
	ALPHA = clamp((base_opacity + mark * 0.30 + edge * 0.045) * glass_visible, 0.0, 0.45);
	ROUGHNESS = 0.34;
	SPECULAR = 0.12;
}
