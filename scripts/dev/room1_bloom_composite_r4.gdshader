shader_type canvas_item;
render_mode unshaded, blend_add;

uniform sampler2D near_halo : filter_linear, repeat_disable;
uniform sampler2D far_halo : filter_linear, repeat_disable;
uniform float strength = 1.0;

void fragment() {
	vec3 near_light = texture(near_halo, UV).rgb;
	vec3 far_light = texture(far_halo, UV).rgb;
	COLOR = vec4((near_light * 0.35 + far_light * 1.4) * strength, 1.0);
}
