"""Measure forefoot travel at three visually identified loading/contact poses."""
import json
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw

root=Path(__file__).resolve().parent
def toes(frame):
    im=Image.open(root/"text16"/f"{frame:02}.png").convert("RGBA")
    foot=np.asarray(im)[116:,:,3] > 127
    # At these three double-support poses x=58 is in the gap between feet.
    assert not foot[:,58].any()
    return [int(np.nonzero(foot[:,:58])[1].min()),58+int(np.nonzero(foot[:,58:])[1].min())]
contacts=[5,10,17]
points=[toes(i) for i in contacts]
lengths_px=[points[i+1][1]-points[i][0] for i in range(2)]
lengths_m=[x*1.65/125 for x in lengths_px]
period=sum(lengths_m)/2.0
targets=np.linspace(5,17,8,endpoint=False)
samples=np.floor(targets+0.5).astype(int).tolist()
data=dict(source="text16", contacts=contacts, toe_x=points, step_px=lengths_px, step_m=lengths_m,
          seconds_per_step_at_2ms=[x/2 for x in lengths_m], average_step_m=sum(lengths_m)/2,
          period_s=period, fps=8/period, source_sample_times=targets.tolist(), samples=samples, hem_guide=85)
(root/"gait.json").write_text(json.dumps(data,indent=2),encoding="utf-8")
proof=Image.new("RGB",(384*3,150),"#343939")
d=ImageDraw.Draw(proof)
for idx,(n,pts) in enumerate(zip(contacts,points)):
    im=Image.open(root/"text16"/f"{n:02}.png").crop((0,94,128,128)).resize((384,102),Image.Resampling.NEAREST)
    proof.paste(im,(idx*384,16),im)
    for x in pts:
        xp=idx*384+x*3
        d.line((xp,119,xp,129),fill="yellow")
        d.text((xp-6,131),str(x),fill="white")
    d.text((idx*384+8,2),f"source {n:02}",fill="white")
proof.save(root/"foot_contacts.png")
print(data)
