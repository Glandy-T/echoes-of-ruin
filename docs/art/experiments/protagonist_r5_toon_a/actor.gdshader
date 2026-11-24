shader_type spatial;
render_mode unshaded;

// B's garment ramp. source_color keeps the palette in the renderer's color space.
uniform sampler2D pigment : source_color, filter_nearest, repeat_disable;
uniform vec4 warm : source_color = vec4(0.90588235,0.87450980,0.81176471,1.0);
uniform vec4 midtone : source_color = vec4(0.74509804,0.71372549,0.65490196,1.0);
uniform vec4 shadow_tint : source_color = vec4(0.50196078,0.56470588,0.54901961,1.0);
uniform bool room_mode = true;
uniform float strip_on : hint_range(0,1) = 1.0;
uniform vec3 neutral_direction = vec3(0.55,0.65,0.52);
uniform vec3 actor_center = vec3(10.5,0.75,-4.75);
varying vec3 position_world;
varying vec3 normal_world;

void vertex() {
    position_world = (MODEL_MATRIX * vec4(VERTEX,1.0)).xyz;
    normal_world = MODEL_NORMAL_MATRIX * NORMAL;
}

void fragment() {
    vec3 n = normalize(normal_world);
    float facing = dot(n,normalize(neutral_direction));
    vec3 illuminant = vec3(1.0);
    if (room_mode) {
        float weight = 0.0;
        float irradiance = 0.0;
        float ribbon = 0.0;
        for (int i=0; i<8; i++) {
            float x=mix(0.205,20.795,(float(i)+0.5)/8.0);
            for (int j=0; j<2; j++) {
                vec3 lamp=vec3(x,3.05,mix(-0.205,-9.295,float(j)));
                vec3 d=lamp-position_world;
                float w=1.0/(1.0+dot(d,d));
                irradiance+=w*max(dot(n,normalize(d)),0.0);
                weight+=w;
                vec3 c=lamp-actor_center;
                ribbon+=1.0/(1.0+0.18*dot(c,c));
            }
        }
        facing=strip_on*irradiance/max(weight,0.00001);
        float level=0.10+strip_on*(0.13+0.38*clamp(ribbon*0.5,0.0,1.0));
        illuminant=vec3(0.78,0.91,1.0)*level;
    }
    float lower=room_mode ? 0.20 : 0.05;
    float upper=room_mode ? 0.36 : 0.55;
    vec3 ramp=mix(shadow_tint.rgb,midtone.rgb,step(lower,facing));
    ramp=mix(ramp,warm.rgb,step(upper,facing));
    ALBEDO=texture(pigment,UV).rgb*(ramp/warm.rgb)*illuminant;
}

