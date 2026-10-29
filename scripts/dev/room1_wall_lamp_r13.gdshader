shader_type spatial;

// r5 is intentionally a superset of r2: mode 0 executes r2's retained local
// sample branch exactly, while modes 1-3 replace only the listed whole-room
// receiver faces. Lighting, UV2 irradiance and capsule occlusion stay shared.
uniform sampler2D color_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D emission_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D strip_irradiance : filter_linear, repeat_disable;
uniform sampler2D wall_structure_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D floor_structure_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D full_wall_left_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D full_wall_right_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D full_wall_front_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D full_wall_rear_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D full_floor_aged_map : source_color, filter_nearest, repeat_disable;
uniform sampler2D full_floor_leaks_map : source_color, filter_nearest, repeat_disable;
uniform vec4 base_color : source_color = vec4(1.0);
uniform float has_emission_map = 0.0;
uniform float uniform_strip_emission = 0.0;
uniform float diffuser_radiance_scale = 1.0;
uniform float strip_surface_energy = 0.7;
uniform float baked_energy = 1.2;
uniform vec3 actor_feet = vec3(10.5, 0.0, -4.75);
uniform float actor_shadow_enabled = 1.0;
uniform vec3 capsule_a;
uniform vec3 capsule_b;
uniform int structure_kind = 0;
uniform float structure_enabled = 0.0;
uniform float base_color_preview = 0.0;
// 0=old r4 local branch, 1=whole walls, 2=walls+aged floor, 3=walls+leaks.
uniform int full_surface_mode = 0;
// 1=floor, 2=left, 3=right, 4=front, 5=rear/header.
uniform int full_surface_kind = 0;
varying vec3 world_position;
varying vec3 world_normal;
void vertex(){ world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; world_normal=normalize(MODEL_NORMAL_MATRIX*NORMAL); }
float capsule_visibility(vec3 origin,vec3 destination){vec3 a=capsule_a;vec3 b=capsule_b;vec3 d1=destination-origin;vec3 d2=b-a;vec3 r=origin-a;float aa=dot(d1,d1);float ee=dot(d2,d2);float ff=dot(d2,r);float cc=dot(d1,r);float bb=dot(d1,d2);float denominator=max(aa*ee-bb*bb,0.000001);float s=clamp((bb*ff-cc*ee)/denominator,0.0,1.0);float t=(bb*s+ff)/ee;if(t<0.0){t=0.0;s=clamp(-cc/aa,0.0,1.0);}else if(t>1.0){t=1.0;s=clamp((bb-cc)/aa,0.0,1.0);}float separation=length(origin+d1*s-a-d2*t);return smoothstep(0.19,0.25,separation);}
void ribbon_sample(vec3 light_position,vec3 emitter_normal,inout float visible_weight,inout float weight_sum){vec3 ray=light_position-world_position;float distance_squared=max(dot(ray,ray),0.01);vec3 direction=ray/sqrt(distance_squared);float facing=max(dot(normalize(world_normal),direction),0.0);float emitting=abs(dot(emitter_normal,-direction));float weight=facing*emitting/distance_squared;visible_weight+=weight*capsule_visibility(world_position+normalize(world_normal)*0.004,light_position);weight_sum+=weight;}
float actor_visibility(){if(actor_shadow_enabled<0.5||distance(world_position.xz,actor_feet.xz)>6.0||world_position.y>actor_feet.y+1.7)return 1.0;float visible_weight=0.0;float weight_sum=0.0;for(int i=0;i<16;i++){float u=(float(i)+0.5)/16.0;float x=mix(0.205,20.795,u);float z=mix(-0.205,-9.295,u);ribbon_sample(vec3(x,3.05,-0.205),vec3(0.0,0.0,-1.0),visible_weight,weight_sum);ribbon_sample(vec3(x,3.05,-9.295),vec3(0.0,0.0,1.0),visible_weight,weight_sum);float saved_visible=visible_weight;float saved_sum=weight_sum;ribbon_sample(vec3(0.205,3.05,z),vec3(1.0,0.0,0.0),visible_weight,weight_sum);ribbon_sample(vec3(20.795,3.05,z),vec3(-1.0,0.0,0.0),visible_weight,weight_sum);visible_weight=saved_visible+(visible_weight-saved_visible)*0.441;weight_sum=saved_sum+(weight_sum-saved_sum)*0.441;}return mix(0.18,1.0,visible_weight/max(weight_sum,0.000001));}
float patch_edge(vec2 uv){vec2 nearest=min(uv,vec2(1.0)-uv);return smoothstep(0.0,0.06,min(nearest.x,nearest.y));}
float patch_edge_x(float u){return smoothstep(0.0,0.015,min(u,1.0-u));}
void fragment(){
 vec3 color=texture(color_map,UV).rgb*base_color.rgb;
 // Retained r2 local branch: needed for an exact r4 mode-0 baseline.
 if(structure_enabled>0.5){vec2 patch_uv=vec2(-2.0);if(structure_kind==1&&world_normal.y>0.9){patch_uv=(world_position.xz-vec2(0.2,-6.4))/vec2(3.2,3.2);if(all(greaterThanEqual(patch_uv,vec2(0.0)))&&all(lessThanEqual(patch_uv,vec2(1.0))))color=mix(color,texture(floor_structure_map,patch_uv).rgb*base_color.rgb,patch_edge(patch_uv));}else if(structure_kind==2&&world_normal.x>0.9){patch_uv=vec2((-world_position.z-3.2)/3.2,1.0-world_position.y/3.4);if(all(greaterThanEqual(patch_uv,vec2(0.0)))&&all(lessThanEqual(patch_uv,vec2(1.0))))color=mix(color,texture(wall_structure_map,patch_uv).rgb*base_color.rgb,patch_edge_x(patch_uv.x));}}
 if(full_surface_mode>=1&&full_surface_kind>=2){float v=1.0-world_position.y/3.4;vec2 wall_uv=full_surface_kind<=3?vec2((-world_position.z-0.2)/9.1,v):vec2((world_position.x-0.2)/20.6,v);if(all(greaterThanEqual(wall_uv,vec2(0.0)))&&all(lessThanEqual(wall_uv,vec2(1.0)))){if(full_surface_kind==2)color=texture(full_wall_left_map,wall_uv).rgb*base_color.rgb;else if(full_surface_kind==3)color=texture(full_wall_right_map,wall_uv).rgb*base_color.rgb;else if(full_surface_kind==4)color=texture(full_wall_front_map,wall_uv).rgb*base_color.rgb;else color=texture(full_wall_rear_map,wall_uv).rgb*base_color.rgb;}}
 if(full_surface_mode>=2&&full_surface_kind==1&&world_normal.y>0.9){vec2 floor_uv=vec2((world_position.x-0.2)/20.6,(world_position.z+9.3)/9.1);if(all(greaterThanEqual(floor_uv,vec2(0.0)))&&all(lessThanEqual(floor_uv,vec2(1.0))))color=(full_surface_mode>=3?texture(full_floor_leaks_map,floor_uv):texture(full_floor_aged_map,floor_uv)).rgb*base_color.rgb;}
 if(base_color_preview>0.5){ALBEDO=vec3(0.0);EMISSION=color;ROUGHNESS=1.0;SPECULAR=0.0;}else{ALBEDO=color;ROUGHNESS=0.95;SPECULAR=0.08;EMISSION=color*texture(strip_irradiance,UV2).rgb*baked_energy*actor_visibility();vec3 diffuser=texture(emission_map,UV).rgb*has_emission_map;float diffuser_mask=uniform_strip_emission*step(0.00001,max(diffuser.r,max(diffuser.g,diffuser.b)));EMISSION*=1.0-diffuser_mask;vec3 lamp_radiance=diffuser*strip_surface_energy*mix(1.0,diffuser_radiance_scale,uniform_strip_emission);
 // The old diffuser exceeded display white, hiding all material texture.
 // Modulate only the visible luminous surface with the PixelLab color map.
 // Keep UV2 room irradiance, power toggles and actor shadow calculations intact.
 if(full_surface_mode>=1&&full_surface_kind>=2){
   vec3 clean_diffuser=vec3(0.60382734,0.72305513,0.77582222);
   vec3 pixel_ratio=clamp(color/clean_diffuser,vec3(0.35),vec3(1.15));
   lamp_radiance*=pixel_ratio;
   lamp_radiance=lamp_radiance/(vec3(1.0)+lamp_radiance);
 }
 EMISSION+=lamp_radiance;}
}
