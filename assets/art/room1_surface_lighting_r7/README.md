# Room 1 matching surface irradiance r7

Latest r6 wall colors and r5 aged floor/leak colors rebaked into the unchanged r4 geometry and UV2 layout. 1024 CPU samples, linear 2048² HDR, original four emitters. Receiving albedo excluded from irradiance; diffuse bounce uses current surface colors.

Run `scenes/dev/room1_surface_lighting_r7.tscn`. I compares old/new irradiance. Color maps and special pod shaders remain unchanged. GLB/mapping/UV2 layout are byte-identical to r4. GLB retains its original embedded colors; the Godot scene binds the current world-projected maps, so this folder alone is not a standalone material replacement.

[Packed Blender source and verification](../../../docs/art/experiments/room1_surface_lighting_r7/README.md). Raw EXR stays local; runtime uses `strip_irradiance_denoised.exr`. Preserve linear HDR and disabled mesh compression import settings.
