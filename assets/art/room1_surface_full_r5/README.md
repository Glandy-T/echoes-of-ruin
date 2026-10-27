# Room 1 full-room surface candidate r5

2026-10-27. Whole-room color maps for the accepted r4 wall approach, seamless aged blue-gray floor, and four pod-anchored old leak residues. No new geometry, UV2, lights, pod design or layout.

- `wall_left.png`, `wall_right.png`: 728×272; `wall_front.png`, `wall_rear.png`: 1648×272. Four individual full-wall maps, not repeated local samples. All use common diffuser and corner edge profiles. Rear door wall pieces share one world-X map.
- `floor_aged.png`, `floor_with_leaks.png`: 1648×728. Full floor world mapping, rear at image top. No tile or route seams. Fixed leak sites P03/P06/P13/P18; seed 20261027, no runtime randomness.
- Canonical PNGs are visible exports from the six editable Aseprite masters. Source layers and reproduction scripts are retained in [the experiment](../../../docs/art/experiments/room1_surface_full_r5/README.md).
- Run `scenes/dev/room1_surface_full_r5.tscn` separately. Formal main entry stays as before. M compares baseline / walls / walls+aged floor / walls+aged floor+leaks. N is color-only diagnosis; J returns to the review station.
- Nearest color-map sampling; 80 texels/m is a trial density. Reuses existing r4 geometry and irradiance. New albedo-dependent indirect bounce has not been rebaked; this is a surface review candidate.

Project-authored pixel layers; no new AI/PixelLab requests and no copied reference pixels this round. Current r5 whole-room appearance awaits user review.
