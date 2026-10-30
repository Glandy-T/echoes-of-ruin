"""Inspection sheets only; these images never become runtime material inputs."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
layout=json.loads((HERE/'tile_layout.json').read_text());rows=[];signatures={}
selection=json.loads((HERE/'selection.json').read_text()) if (HERE/'selection.json').exists() else {}
for row in range(3):
    sheet=Image.new('RGB',(256*7,276),(22,34,38));draw=ImageDraw.Draw(sheet)
    for tile in layout['tiles']:
        if tile['row']!=row:continue
        actual=selection.get(tile['name'],tile['name']);p=EXP/'raw'/f'{actual}.png'
        if not p.exists():continue
        raw=np.array(Image.open(p).convert('RGBA'))
        guide=np.asarray(Image.open(HERE/f"guide_{tile['name']}.png").convert('RGBA'))
        mask=np.asarray(Image.open(HERE/f"mask_{tile['name']}.png").convert('L'))>0
        # Black-masked AI inventions are not material; show the exact protected
        # input pixels there, just as the runtime composition does.
        shown=raw.copy();shown[~mask]=guide[~mask]
        sheet.paste(Image.fromarray(shown).convert('RGB'),(tile['column']*256,20))
        draw.text((tile['column']*256+4,2),actual+' native / protected exact',fill=(223,232,224))
        signatures[tile['name']]=hashlib.sha256(p.read_bytes()).hexdigest()
    sheet.save(HERE/f'native_row_{row+1}_review.png')
report={'ready_originals':len(signatures),'distinct_raw_hashes':len(set(signatures.values())),'hashes':signatures,'meaning':'duplicate hash screen only; art/repetition require actual native/whole-floor and game-camera review','resampling':False,'protected_AI_pixels_not_used':True}
(HERE/'native_source_screen.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('R26_NATIVE_REVIEW',len(signatures),'ready unique raw hashes',len(set(signatures.values())))
