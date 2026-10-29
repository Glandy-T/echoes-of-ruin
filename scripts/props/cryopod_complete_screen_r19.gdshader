shader_type spatial;
uniform sampler2D screen_pixels : source_color, filter_nearest, repeat_disable;
uniform sampler2D screen_overlay : source_color, filter_nearest, repeat_disable;
uniform float core_energy = 2.0;
uniform float powered = 1.0;
uniform float warning_red = 0.0;
uniform vec4 panel_tint : source_color = vec4(0.321569,0.423529,0.462745,1.0);
uniform float panel_backlight = 0.8;
uniform float progress = 0.0;
uniform float secondary_progress = 0.0;
uniform float tertiary_progress = 0.0;
void fragment() {
	// Edge-to-edge display substrate: the old painted bezel is not screen content.
	vec3 pixels = texture(screen_pixels, vec2(100.0/128.0,10.0/48.0)).rgb;
	// One source pixel of perimeter seal, with a flat full-width LCD beneath.
	float content = step(1.0/128.0,UV.x)*(1.0-step(127.0/128.0,UV.x))*step(1.0/48.0,UV.y)*(1.0-step(47.0/48.0,UV.y));
	float inside_x=step(8.0/128.0,UV.x)*(1.0-step(120.0/128.0,UV.x));
	float text_rows=(step(7.0/48.0,UV.y)*(1.0-step(16.0/48.0,UV.y))+step(20.0/48.0,UV.y)*(1.0-step(30.0/48.0,UV.y)))*inside_x;
	vec3 background=texture(screen_pixels,vec2(100.0/128.0,10.0/48.0)).rgb;
	pixels=mix(pixels,background,clamp(text_rows,0.0,1.0));
	float bar_x=step(10.0/128.0,UV.x)*(1.0-step(108.0/128.0,UV.x));
	float upper_bar=step(18.0/48.0,UV.y)*(1.0-step(20.0/48.0,UV.y))*bar_x;
	float middle_bar=step(32.0/48.0,UV.y)*(1.0-step(35.0/48.0,UV.y))*bar_x;
	float lower_bar=step(38.0/48.0,UV.y)*(1.0-step(40.0/48.0,UV.y))*bar_x;
	vec3 track=texture(screen_pixels,vec2(105.0/128.0,33.0/48.0)).rgb;
	vec3 fill=texture(screen_pixels,vec2(105.0/128.0,19.0/48.0)).rgb;
	pixels=mix(pixels,track,clamp(upper_bar+middle_bar+lower_bar,0.0,1.0));
	float progress_row=upper_bar*step(UV.x,mix(10.0/128.0,108.0/128.0,clamp(progress,0.0,1.0)))+middle_bar*step(UV.x,mix(10.0/128.0,108.0/128.0,clamp(secondary_progress,0.0,1.0)))+lower_bar*step(UV.x,mix(10.0/128.0,108.0/128.0,clamp(tertiary_progress,0.0,1.0)));
	vec4 overlay = texture(screen_overlay, UV);
	vec3 state = mix(mix(pixels,fill,progress_row), overlay.rgb, overlay.a);
	float brightness=max(state.r,max(state.g,state.b));
    state=mix(state,vec3(1.0,0.075,0.025)*brightness,warning_red);
	float glyphs=smoothstep(0.28,0.52,brightness);
	ALBEDO = mix(vec3(0.035,0.055,0.065),state,content) * mix(0.12, mix(0.3, 1.0, glyphs + progress_row), powered);
	ROUGHNESS = 0.8;
	SPECULAR = 0.0;
	EMISSION = state * vec3(0.75, 0.95, 1.0) * core_energy * max(glyphs, progress_row) * content * powered;
	// Full panel substrate; the separate real housing is unchanged. Power-off has no glow.
	float background_mask=1.0-smoothstep(0.10,0.30,brightness);
	EMISSION+=panel_tint.rgb*panel_backlight*background_mask*content*powered;
}
