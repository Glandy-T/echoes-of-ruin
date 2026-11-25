"""Export an original-scale gameplay crop from the six actual viewport captures."""
from pathlib import Path
from tempfile import gettempdir
from PIL import Image
from build_fix import OUT, loop

folder = Path(gettempdir()) / "eor_idle45_breath_r3_review"
frames = []
for n in range(1, 7):
    shot = Image.open(folder / f"45_{n:02}.png").convert("RGB")
    assert shot.size == (1280,720)
    frames.append(shot.crop((535,244,745,510)))
atlas = Image.new("RGB", (210,266*6))
for n, frame in enumerate(frames):
    atlas.paste(frame,(0,266*n))
palette = atlas.quantize(colors=256)
loop([im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames], OUT/"room_native.gif")
