# Reference silhouette measurement notes

These values were measured by importing the user-supplied GLB only into a
temporary Blender session.  The source mesh was not saved, exported or used as
an asset here.

## Normalized reference envelope

| Item | Source measure | Ratio to main shell | When length is 2.30 m |
| --- | ---: | ---: | ---: |
| Main shell width | 0.24096 | 1.000 | 1.05 m fixed target |
| Main shell length | 0.54021 | 1.000 | 2.30 m |
| Main shell height | 0.15398 | 0.639 width | about 0.67 m |
| Top cover/window width | 0.21484 | 0.892 width | about 0.94 m |
| Top cover/window length | 0.36999 | 0.685 length | about 1.58 m |
| Top cover/window height | 0.04644 | 0.302 shell height | about 0.20 m vertical span |

The main shell's highest measured edge is `1.000H`; the cover's highest point
is `0.981H`.  The cover therefore sits nearly flush within the shell's upper
edge, rather than forming a raised capsule roof.

## Long-axis landmarks

Source-Y is the long axis in the inspection renders.  The side image is shown
from positive X, so negative Y is on the left of `01_side_silhouette.png`.

| Normalized long-axis interval | At 2.30 m | Form to preserve |
| --- | --- | --- |
| 0.000–0.188 | 0.00–0.43 m | Deep, slanted end fascia and the start of the raised upper rim. |
| 0.188–0.873 | 0.43–2.01 m | Inset window/cover bay.  It has straight long rails and a wide planar window field. |
| 0.873–1.000 | 2.01–2.30 m | Short rounded end cap with a downward side transition. |

At the middle of the cover bay, the side-shell upper rail is about `0.68H`
(about `0.46 m` if total height is 0.67 m).  The window/cover rises from that
rail to roughly `0.98H` (about `0.66 m`).  The local perimeter rim can reach
`1.00H` (about `0.67 m`).

## Geometry versus later pixel paint

Model the two unequal end masses, lower plinth, large side wall, continuous
top frame, cover/window boundary and broad end-facing panel.  Leave the long
side vent, small catches, small control plate, visible tank and fine rails out
of the v4 grey model; they do not determine the silhouette and can be handled
as texture motifs if retained later.
