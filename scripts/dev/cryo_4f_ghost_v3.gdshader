shader_type spatial;
uniform sampler2D color_map : source_color, filter_nearest, repeat_enable;
uniform sampler2D emission_map : source_color, filter_nearest, repeat_enable;
uniform sampler2D irradiance_map : filter_linear, repeat_disable;
uniform float lamp_power = 1.0;
uniform float is_wall = 0.0;
uniform float baked_energy = 1.2;
uniform float opacity = 1.0;
void fragment(){
 vec3 color=texture(color_map,UV).rgb;
 vec3 diffuser=texture(emission_map,UV).rgb*is_wall;
 float mask=step(.00001,max(diffuser.r,max(diffuser.g,diffuser.b)));
 vec3 light=color*texture(irradiance_map,UV2).rgb*baked_energy*(1.0-mask);
 vec3 lamp=diffuser*(20.0*.06/.225)*.7;lamp=lamp/(vec3(1.0)+lamp);
 ALBEDO=vec3(0.0);EMISSION=(light+lamp)*lamp_power;ROUGHNESS=.95;SPECULAR=.08;ALPHA=opacity;
}
