"""Assemble actual Godot captures; no asset or texture painting."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

base=Path(__file__).resolve().parent.parent
out=base/'evidence'
cap=out/'godot'

def image(name):
    with Image.open(cap/(name+'.png')) as im:
        assert im.size==(1280,720), name
        return im.convert('RGB')

def contact(rows, name, width=640):
    height=width*9//16
    sheet=Image.new('RGB',(2*width,(height+25)*len(rows)), '#172125')
    draw=ImageDraw.Draw(sheet)
    for row, names in enumerate(rows):
        for col, shot in enumerate(names):
            x=col*width
            y=row*(height+25)
            draw.text((x+8,y+6),shot,fill='#f0f5f0')
            sheet.paste(image(shot).resize((width,height),Image.Resampling.LANCZOS),(x,y+25))
    sheet.save(out/(name+'.png'),optimize=True)

contact([
    ('hr-a_rail','hr-b_rail'),
    ('fd-a_closed','fd-b_closed'),
    ('el-a_caution','el-b_caution'),
    ('en-a_transition','en-b_transition'),
    ('fa-a_overall','fa-b_overall'),
], 'candidate_contact',480)
contact([
    ('hr-a_occupied','hr-b_occupied'),('fd-a_open90','fd-b_sweep'),
    ('el-a_touch','el-b_pass'),('en-a_rear','en-b_open90'),
    ('fa-a_detail10m','fa-b_detail10m'),('fa-a_roof','fa-b_b4'),
], 'detail_contact',480)

if __name__=='__main__':
    records=json.loads((cap/'capture_record.json').read_text(encoding='utf8'))
    motion=[r for r in records if r['file'].startswith('stair_motion_')]
    assert len(motion)==112 and len(records)==len({r['file'] for r in records})
    assert all(not r['missing_textures'] for r in records)
    frames=[]
    for rec in motion:
        frame=image(rec['file'][:-4])
        frames.append(frame.quantize(192,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE))
    frames[0].save(out/'stair_motion_28s.gif',save_all=True,append_images=frames[1:],duration=250,loop=0,optimize=True,disposal=1)
    with Image.open(out/'stair_motion_28s.gif') as gif:
        duration=0
        for idx in range(gif.n_frames):
            gif.seek(idx)
            duration+=gif.info['duration']
        assert duration==28000
    print(f"{len(records)} unique Godot captures, {len(motion)} frames, {duration/1000:g}s playback")
