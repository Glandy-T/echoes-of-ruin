"""Read Aseprite visible cels back and verify they match the delivered PNGs."""
from pathlib import Path
from PIL import Image
import struct,zlib,hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[3]
def read_aseprite(path):
    data=path.read_bytes();u16=lambda off:struct.unpack_from('<H',data,off)[0]
    assert u16(4)==0xA5E0 and u16(6)==1 and u16(12)==32
    w,h=u16(8),u16(10);layers=[];cels=[];pos=128
    frame_size=struct.unpack_from('<I',data,pos)[0];assert u16(pos+4)==0xF1FA
    count=struct.unpack_from('<I',data,pos+12)[0] or u16(pos+6);pos+=16
    for _ in range(count):
        size,kind=struct.unpack_from('<IH',data,pos);chunk=data[pos+6:pos+size]
        if kind==0x2004:
            flags,typ,level=struct.unpack_from('<HHH',chunk,0)
            blend=struct.unpack_from('<H',chunk,10)[0];length=struct.unpack_from('<H',chunk,16)[0]
            layers.append({'name':chunk[18:18+length].decode('utf-8'),'visible':bool(flags&1),'type':typ,'level':level,'blend':blend,'opacity':chunk[12]})
        elif kind==0x2005:
            layer,x,y,opacity,typ=struct.unpack_from('<HhhBH',chunk,0)
            assert typ in [0,2]
            cw,ch=struct.unpack_from('<HH',chunk,16)
            pixels=zlib.decompress(chunk[20:]) if typ==2 else chunk[20:]
            cels.append((layer,x,y,opacity,Image.frombytes('RGBA',(cw,ch),pixels)))
        pos+=size
    assert pos==128+frame_size
    result=Image.new('RGBA',(w,h),(0,0,0,0))
    for index,x,y,opacity,image in cels:
        layer=layers[index]
        if not layer['visible']:continue
        assert layer['blend']==0 and layer['opacity']==255 and opacity==255
        canvas=Image.new('RGBA',(w,h),(0,0,0,0));canvas.paste(image,(x,y));result=Image.alpha_composite(result,canvas)
    return result.convert('RGB'),layers

records={}
for key in ['wall','floor']:
    source=ROOT/'editable'/f'{key}_structure_r2.aseprite'
    image,layers=read_aseprite(source)
    exported=Image.open(PROJECT/'assets/art/room1_surface_structure_r2'/f'{key}_sample.png').convert('RGB')
    assert image.size==exported.size
    difference=np.abs(np.asarray(image,dtype=int)-np.asarray(exported,dtype=int))
    assert difference.max()==0,(key,int(difference.max()))
    assert len(layers)==(6 if key=='wall' else 4)
    assert not layers[-1]['visible'] and not layers[-2]['visible']
    records[key]={'size':list(image.size),'layers':layers,'visible_composite_matches_png':True,'max_channel_difference':int(difference.max()),'aseprite_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
scope={}
for name in ['assets/art/room1_wall_finish_r4/room1_baked_uv2_r3.glb','assets/art/room1_wall_finish_r4/strip_irradiance_denoised.exr','assets/art/room1_wall_finish_r4/mesh_mapping.json','assets/art/room1_revision_20261013/pod_closed_v3.glb','scripts/dev/room1_pod_exit_animation_r3.gd','project.godot']:
    file=PROJECT/name;scope[name]={'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'bytes':file.stat().st_size}
(ROOT/'source/verification.json').write_text(json.dumps({'aseprite_readback':records,'inherited_sources':scope,'scope':'Source verification only; runtime screenshots and user art review remain separate.'},indent=2),encoding='utf-8')
print('Both layered Aseprite visible composites exactly match exported PNGs; hidden guides/raw retained.')
