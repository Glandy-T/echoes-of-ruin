"""Package two editable layers using the approved sprite's 128px RGBA file layout."""
from pathlib import Path
import struct, zlib, json
from PIL import Image

root=Path(__file__).resolve().parent
gait=json.loads((root/"gait.json").read_text())
template=(root.parent/"protagonist_five_idle_eyes_r3/final_90.aseprite").read_bytes()
header=bytearray(template[:128])
assert struct.unpack_from("<5H",header,4)==(0xA5E0,1,128,128,32)
def chunk(kind,body):
    return struct.pack("<IH",len(body)+6,kind)+body
defaults=[]
pos=144
while pos<len(template):
    size,kind=struct.unpack_from("<IH",template,pos)
    if kind in (0x2007,0x2019):
        defaults.append(template[pos:pos+size])
    pos+=size
def layer(name,flags):
    name=name.encode()
    return chunk(0x2004,struct.pack("<6HB3xH",flags,0,0,0,0,0,255,len(name))+name)
def cel(index,pixels):
    return chunk(0x2005,struct.pack("<HhhBH7xHH",index,0,0,255,2,128,128)+zlib.compress(pixels,9))
out=bytearray()
for j,n in enumerate(gait["samples"]):
    parts=[] if j else defaults+[layer("PixelLab raw",2),layer("Floor aligned",3)]
    for k,path in enumerate([root/gait["source"]/f"{n:02}.png",root/f"cycle_{j+1:02}.png"]):
        parts.append(cel(k,Image.open(path).convert("RGBA").tobytes()))
    payload=b"".join(parts)
    ms=gait["period_s"]*1000/8
    dur=round((j+1)*ms)-round(j*ms)
    out+=struct.pack("<IHHH2xI",16+len(payload),0xF1FA,len(parts),dur,len(parts))+payload
struct.pack_into("<I",header,0,128+len(out))
struct.pack_into("<H",header,6,8)
struct.pack_into("<H",header,18,round(ms))
path=root/"walk.aseprite"
path.write_bytes(header+out)
data=path.read_bytes()
pos=128
for j,n in enumerate(gait["samples"]):
    size,magic,count=struct.unpack_from("<IHH",data,pos)
    assert magic==0xF1FA
    start=pos
    pos+=16
    for k in range(count):
        length,kind=struct.unpack_from("<IH",data,pos)
        if kind==0x2005:
            idx=struct.unpack_from("<H",data,pos+6)[0]
            path=root/f"cycle_{j+1:02}.png" if idx else root/gait["source"]/f"{n:02}.png"
            assert zlib.decompress(data[pos+26:pos+length])==Image.open(path).convert("RGBA").tobytes()
        pos+=length
    assert pos==start+size
assert pos==len(data)
