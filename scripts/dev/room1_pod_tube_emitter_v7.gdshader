shader_type spatial;
uniform float tube_powered=1.0;
void fragment(){
	ALBEDO=vec3(.18,.23,.24);ROUGHNESS=.85;SPECULAR=0.0;
	EMISSION=vec3(.58,.76,.80)*.65*tube_powered;
}
