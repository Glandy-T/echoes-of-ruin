shader_type spatial;
render_mode unshaded;
uniform sampler2D color_map : source_color, filter_nearest, repeat_disable;
uniform vec4 base_color : source_color = vec4(1.0);
void fragment(){ALBEDO=texture(color_map,UV).rgb*base_color.rgb;ROUGHNESS=1.0;SPECULAR=0.0;}
