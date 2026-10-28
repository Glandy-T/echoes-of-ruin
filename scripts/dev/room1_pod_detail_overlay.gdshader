shader_type canvas_item;

// The same 128x48 source texture and runtime label used by the P12 display.
// Mirrors the v8.1 screen layout without the old painted bezel.
uniform sampler2D screen_overlay : source_color, filter_nearest, repeat_disable;
uniform vec4 panel_tint : source_color = vec4(0.321569, 0.423529, 0.462745, 1.0);
uniform float panel_backlight = 0.8;
uniform float progress = 0.0;
uniform float secondary_progress = 0.0;
uniform float tertiary_progress = 0.0;

void fragment() {
	float content = step(1.0/128.0, UV.x) * (1.0-step(127.0/128.0, UV.x)) * step(1.0/48.0, UV.y) * (1.0-step(47.0/48.0, UV.y));
	vec3 pixels = texture(TEXTURE, vec2(100.0/128.0, 10.0/48.0)).rgb;
	float bar_x = step(10.0/128.0, UV.x) * (1.0-step(108.0/128.0, UV.x));
	float upper = step(18.0/48.0, UV.y) * (1.0-step(20.0/48.0, UV.y)) * bar_x;
	float middle = step(32.0/48.0, UV.y) * (1.0-step(35.0/48.0, UV.y)) * bar_x;
	float lower = step(38.0/48.0, UV.y) * (1.0-step(40.0/48.0, UV.y)) * bar_x;
	vec3 track = texture(TEXTURE, vec2(105.0/128.0, 33.0/48.0)).rgb;
	vec3 fill = texture(TEXTURE, vec2(105.0/128.0, 19.0/48.0)).rgb;
	pixels = mix(pixels, track, clamp(upper+middle+lower, 0.0, 1.0));
	float filled = upper*step(UV.x,mix(10.0/128.0,108.0/128.0,clamp(progress,0.0,1.0))) + middle*step(UV.x,mix(10.0/128.0,108.0/128.0,clamp(secondary_progress,0.0,1.0))) + lower*step(UV.x,mix(10.0/128.0,108.0/128.0,clamp(tertiary_progress,0.0,1.0)));
	vec4 overlay = texture(screen_overlay, UV);
	vec3 state = mix(mix(pixels, fill, filled), overlay.rgb, overlay.a);
	float brightness = max(state.r, max(state.g, state.b));
	float glyphs = smoothstep(0.28, 0.52, brightness);
	vec3 albedo = mix(vec3(0.035,0.055,0.065), state, content) * mix(0.3, 1.0, clamp(glyphs+filled,0.0,1.0));
	vec3 emission = state * vec3(0.75,0.95,1.0) * max(glyphs,filled) * content;
	emission += panel_tint.rgb * panel_backlight * (1.0-smoothstep(0.10,0.30,brightness)) * content;
	COLOR = vec4(clamp(albedo + emission, 0.0, 1.0), 1.0);
}

