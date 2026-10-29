shader_type canvas_item;
render_mode unshaded, blend_add;
uniform sampler2D near_halo : filter_linear, repeat_disable;
uniform sampler2D far_halo : filter_linear, repeat_disable;
uniform sampler2D visible_core : filter_linear, repeat_disable;
uniform float strength = 1.0;
void fragment(){
    vec3 near_light=texture(near_halo,UV).rgb;
    vec3 far_light=texture(far_halo,UV).rgb;
    vec3 core=texture(visible_core,UV).rgb;
    // Scatter around the lens without repainting/overexposing its core.
    vec3 scatter=max(near_light*1.15+far_light*0.65-core*0.45,vec3(0.0));
    COLOR=vec4(scatter*strength,1.0);
}
