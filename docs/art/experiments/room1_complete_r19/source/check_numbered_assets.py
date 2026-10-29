"""Verify functional IDs only; no pixel material is created or edited here."""
from pathlib import Path
import hashlib, json, re
import numpy as np
from PIL import Image, ImageDraw

here = Path(__file__).resolve().parent
root = here.parents[4]
records = json.loads((here / "layout_before.json").read_text(encoding="utf-8"))["pods"]
helper = (root / "scripts/props/cryopod_material_variants_r16.gd").read_text(encoding="utf-8")
digits = json.loads(re.search(r"const DIGITS := (\[[^\n]+\])", helper)[1])
plates = {"lid":(47,197,33,14), "shell_end":(55,35,18,14)}
starts = {"lid":(55,198), "shell_end":(57,37)}
rows, unique = [], {"lid":set(), "shell_end":set()}
for record in records:
    for role in plates:
        number = record["number"]
        source = root / "assets/art/room1_pod_pixellab_r16" / ("variant_"+"abcd"[record["variant_index"]]) / (role+".png")
        expected = Image.open(source).convert("RGBA")
        if number != 12:
            draw = ImageDraw.Draw(expected)
            x,y,w,h = plates[role]
            draw.rectangle((x,y,x+w-1,y+h-1), fill=(190,199,194,255))
            sx,sy = starts[role]
            for i,digit in enumerate(f"{number:02d}"):
                for cy in range(5):
                    for cx in range(3):
                        if digits[int(digit)][cy*3+cx] == "1":
                            px,py=sx+i*8+cx*2,sy+cy*2
                            draw.rectangle((px,py,px+1,py+1),fill=(34,51,64,255))
        actual = Image.open(root / record["bake_color_maps"][role]).convert("RGBA")
        assert np.array_equal(np.asarray(actual),np.asarray(expected)), (record["id"],role)
        x,y,w,h = plates[role]
        unique[role].add(hashlib.sha256(actual.crop((x,y,x+w,y+h)).tobytes()).hexdigest())
        rows.append({"id":record["id"],"role":role,"exact_expected_number":True,"non_label_pixels_preserved":True})
assert all(len(values)==20 for values in unique.values())
report={"result":"PASS","checked_textures":len(rows),"unique_id_plates":{role:len(values) for role,values in unique.items()},"p12_original_pixels_preserved":True,"checks":rows}
(here/"numbering_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("R19_NUMBERING_PASS: 40 textures; unique 01-20 on both lid/end; material outside labels unchanged.")
