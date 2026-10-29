shader_type spatial;
render_mode unshaded, cull_back;

uniform vec3 phosphor_color : source_color = vec3(0.34,0.82,0.44);
uniform vec3 off_color : source_color = vec3(0.080,0.105,0.100);
uniform float phosphor_energy = 0.78;
uniform float passage_power = 0.0;
uniform float leaf_min_x = -0.695;
uniform float leaf_max_x = 0.695;
varying float jamb_x;
varying float world_height;

void vertex(){
    // Mesh vertices are in the stationary door root, not on the moving leaf.
    jamb_x=VERTEX.x;
    world_height=(MODEL_MATRIX*vec4(VERTEX,1.0)).y;
}
void fragment(){
    // Depth testing handles the real leaf; this coverage guard additionally
    // keeps its head/floor installation clearances from glowing through gaps.
    float exposed=(jamb_x<leaf_min_x || jamb_x>leaf_max_x)?1.0:0.0;
    float falloff=mix(0.30,1.0,smoothstep(0.0,0.90,world_height));
    vec3 inactive=off_color*falloff;
    // The 26mm bevel is a housing, not a 26mm luminous rectangle. A ~9mm
    // opal LED window sits between dark shoulders, with soft lens edges.
    // This is a lighting cross-section; no pixel texture/grime is generated.
    float across=abs(UV.x-0.5);
    float lens=1.0-smoothstep(0.12,0.22,across);
    float core=1.0-smoothstep(0.0,0.12,across);
    float shoulder=1.0-smoothstep(0.20,0.50,across);
    vec3 fluorescent=mix(phosphor_color,vec3(0.58,0.92,0.64),core*0.20)*phosphor_energy;
    vec3 powered=mix(inactive,fluorescent,lens);
    // Very weak lens scatter only on the adjacent physical housing surface.
    powered+=phosphor_color*0.014*shoulder*(1.0-lens);
    ALBEDO=mix(inactive,powered,passage_power*exposed);
    ROUGHNESS=1.0;
    SPECULAR=0.0;
}
