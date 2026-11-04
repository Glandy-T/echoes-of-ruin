shader_type spatial;
uniform sampler2D color_map : source_color, filter_nearest, repeat_enable;
uniform sampler2D emission_map : source_color, filter_nearest, repeat_enable;
uniform sampler2D irradiance_map : filter_linear, repeat_disable;
uniform float lamp_power=1.0;
uniform float is_wall=0.0;
uniform float baked_energy=1.2;
uniform bool plain_surface=false;
uniform vec4 plain_color : source_color=vec4(.045,.065,.065,1.0);
uniform bool clip_foreground=false;
uniform float foreground_edge_z=0.0;
varying vec3 world_point;
void vertex(){world_point=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;}
void fragment(){
 if(clip_foreground && world_point.z<foreground_edge_z)discard;
 vec3 color=texture(color_map,UV).rgb;
 vec3 diffuser=texture(emission_map,UV).rgb*is_wall;
 float mask=step(.00001,max(diffuser.r,max(diffuser.g,diffuser.b)));
 vec3 light=color*texture(irradiance_map,UV2).rgb*baked_energy*(1.0-mask);
 vec3 lamp=diffuser*(20.0*.06/.225)*.7;lamp=lamp/(vec3(1.0)+lamp);
 ALBEDO=vec3(0.0);EMISSION=plain_surface?plain_color.rgb:(light+lamp)*lamp_power;
 ROUGHNESS=.95;SPECULAR=.08;
}
