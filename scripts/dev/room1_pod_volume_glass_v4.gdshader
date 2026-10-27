shader_type spatial;
render_mode blend_mix, cull_back;
uniform sampler2D glass_pixels : source_color, filter_nearest, repeat_disable;
uniform float reflections_enabled = 1.0;
uniform float base_opacity = 0.10;
void fragment(){
 vec4 pixel=texture(glass_pixels,UV);
 // Alpha is deliberately authored independently from RGB, not inferred from tint.
 float mark=clamp((pixel.a-24.0/255.0)/(80.0/255.0),0.0,1.0)*reflections_enabled;
 float edge=pow(1.0-clamp(abs(dot(normalize(NORMAL),normalize(VIEW))),0.0,1.0),3.0);
 ALBEDO=mix(vec3(.13,.21,.25),pixel.rgb,mark*.75);
 ALPHA=clamp(base_opacity+mark*.30+edge*.045,.08,.45);
 ROUGHNESS=.34;SPECULAR=.12;EMISSION=vec3(0.0);
}
