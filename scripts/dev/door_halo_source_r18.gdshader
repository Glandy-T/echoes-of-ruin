shader_type spatial;
render_mode unshaded, cull_back;

uniform vec3 phosphor_color : source_color = vec3(0.34,0.82,0.44);
uniform float phosphor_energy = 0.78;
uniform float passage_power = 0.0;
uniform float leaf_min_x = -0.695;
uniform float leaf_max_x = 0.695;
varying float jamb_x;

void vertex(){ jamb_x=VERTEX.x; }
void fragment(){
    float exposed=(jamb_x<leaf_min_x || jamb_x>leaf_max_x)?1.0:0.0;
    float across=abs(UV.x-0.5);
    float lens=1.0-smoothstep(0.12,0.22,across);
    float core=1.0-smoothstep(0.0,0.12,across);
    vec3 fluorescent=mix(phosphor_color,vec3(0.58,0.92,0.64),core*0.20)*phosphor_energy;
    // Only the already-approved luminous lens enters this mask. Housing and
    // inactive faces are black, so neither can create a door-shaped glow.
    ALBEDO=fluorescent*lens*passage_power*exposed;
}
