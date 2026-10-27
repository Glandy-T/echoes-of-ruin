# Room 1 floor contact aging r8

Continuous aged floor with connected deposits at all four wall-foot edges and twenty measured pod-base outlines. Original r5 leak layers stay above the new layers. `floor_aged.png` omits leaks; `floor_with_leaks.png` is the default. Both are 1648×728 nearest-sampled color maps, exported from 7/10-layer editable Aseprite masters.

Run `scenes/dev/room1_floor_contact_r8.tscn`. F compares r7/r8 floor, I compares r7/r8 irradiance. Original r6 walls, geometry, UV2, emitters, gameplay camera and layout stay unchanged. Matching 1024-sample linear irradiance is included; GLB and mapping remain the existing geometry carrier, and the scene binds current color maps.

[Sources, Blender and validation](../../../docs/art/experiments/room1_floor_contact_r8/README.md). Raw EXR remains local or packed in the editable source; runtime uses denoised EXR. Preserve disabled GLB compression and linear HDR import settings.
