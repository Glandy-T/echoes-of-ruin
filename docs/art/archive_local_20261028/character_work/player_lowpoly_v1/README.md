# Protagonist low-poly trial v1 — visual direction rejected / workflow under review

2026-10-13. This is an unfinished local trial, **not an approved character asset**.
The user described the first render as ghost-like and questioned the modeling workflow.
The later local revision reduced the face-framing hair and corrected the scalp coverage,
but shoulder clipping and unsatisfactory character/art direction remain. Do not use these
files as an accepted master or proceed to animation on this basis.

## Confirmed request

- 1.65 m height; natural proportions.
- Preserve the earlier protagonist's long dark hair, long pale sleep garment, and bare feet.
- No drawn facial features; keep subtle facial volume.
- Static low-poly + provisional pixel textures; final pixel art will replace the drafts.
- Keep body, clothing, and hair editable as separate objects, with explicit UVs/materials.
- Assess compatibility with the Pixel Canals method and current Room 1 art trial.

## Sources

- GitHub main checked at `4c201289a5cb1f730897017d2186765f8d1ca470`.
- `docs/ART_DIRECTION.md` v0.44, `docs/CHARACTER_DESIGN.md`.
- `docs/art/PIXEL_CANALS_REFERENCE.md`; local content SHA256 matches the remote file:
  `572528A96C5F871DAD1E3566544086E4C8CA48E69CCAD37678681927E56A2CAC`.
- Local earlier standing references copied to `references/`. They define the character,
  not the proportions of a third-party model. No third-party model/texture was extracted.
- Room 1 review appends existing `docs/art/experiments/room1_lowpoly_v2/` collections
  into a separate Blender scene; its original source was not changed.

## Current files and boundaries

- `build_character.py`: original scripted mesh trial; creates 23 separate meshes.
- `texture_authoring.py`, `texture_sources.json`: editable original pixel color drafts.
- `textures/`: separate cloth, hair and skin PNGs.
- `uv_guides/`: actual mesh UV wires in SVG; some thickness faces deliberately sample
  a constant color. Shared left/right skin UVs and shared fringe UVs are intentional.
- `player_lowpoly_v1.blend`: native source with character, turnaround and room-fit scenes.
- `player_lowpoly_v1.glb`: selected character only; portable rough-diffuse materials.
- `evidence/`: native Blender camera renders from the current draft, half resolution.
- `asset_manifest.json`: inventory; it is **not independent validation**.

The preview uses Blender EEVEE Shader-to-RGB stepped lighting. This does not export as
an equivalent Godot material. GLB uses separate basic rough-diffuse texture materials.
No skeleton, weights, animation, Godot integration, runtime verification, or completed
topology validation. Clothing sleeves are separate overlapping meshes, not a proven
deformation-ready shoulder junction. Body/skin clipping still needs correction.

The latest pending discussion is whether to replace coordinate-generated anatomy with
a suitable base-mesh and visual modeling workflow. Do not keep changing procedural
dimensions or treat another successful render as visual acceptance.

## Reproduce this trial only

From this directory, with Blender 5.0.1 installed:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' --background --factory-startup --python-exit-code 1 --python .\build_character.py -- --quick
```

The script rewrites only this trial directory's generated outputs. `--quick` renders at
50%; omit it for full resolution. `--skip-render` rebuilds source/export without rendering.
All coordinates are metres, +Z up, front -Y, foot ground at Z=0.
