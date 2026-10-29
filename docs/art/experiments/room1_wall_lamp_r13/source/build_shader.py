"""Expose PixelLab diffuser pixels without changing the existing irradiance."""
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
s=(ROOT/"scripts/dev/room1_surface_full_r5.gdshader").read_text(encoding="utf-8")
old='EMISSION+=diffuser*strip_surface_energy*mix(1.0,diffuser_radiance_scale,uniform_strip_emission);'
new='''vec3 lamp_radiance=diffuser*strip_surface_energy*mix(1.0,diffuser_radiance_scale,uniform_strip_emission);
 // The old diffuser exceeded display white, hiding all material texture.
 // Modulate only the visible luminous surface with the PixelLab color map.
 // Keep UV2 room irradiance, power toggles and actor shadow calculations intact.
 if(full_surface_mode>=1&&full_surface_kind>=2){
   vec3 clean_diffuser=vec3(0.60382734,0.72305513,0.77582222);
   vec3 pixel_ratio=clamp(color/clean_diffuser,vec3(0.35),vec3(1.15));
   lamp_radiance*=pixel_ratio;
   lamp_radiance=lamp_radiance/(vec3(1.0)+lamp_radiance);
 }
 EMISSION+=lamp_radiance;'''
assert s.count(old)==1
(ROOT/"scripts/dev/room1_wall_lamp_r13.gdshader").write_text(s.replace(old,new),encoding="utf-8")
