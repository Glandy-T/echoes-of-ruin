shader_type spatial;
render_mode cull_back;
uniform sampler2D color_map : source_color, filter_nearest, repeat_disable;
uniform vec4 tint : source_color = vec4(1.0);
void fragment(){ ALBEDO=texture(color_map,UV).rgb*tint.rgb;ROUGHNESS=0.94;SPECULAR=0.0; }
void light(){float ndl=max(dot(NORMAL,LIGHT),0.0);float band=ndl>.62?1.0:(ndl>.23?.66:.27);DIFFUSE_LIGHT+=ALBEDO*LIGHT_COLOR*ATTENUATION*band/PI;}
