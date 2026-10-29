"""Mask and layer PixelLab outputs; preserve structure and functional labels."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,argparse
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
ASSET=ROOT/'assets/art/room1_pod_pixellab_r16'
EXTERNAL=['lid','shell_side','shell_end'];SHARED=['interior','mattress','section']
def final_mask(key):
    mask=Image.open(HERE/f'mask_{key}.png').convert('L')
    if key=='shell_side':
        # The accepted top inset is blue-gray; the first AI result recolored it
        # white. Protect that existing structural color zone, never repaint age.
        ImageDraw.Draw(mask).rectangle((0,0,255,25),fill=0)
    if key=='shell_end':
        # One candidate invented a pale patch on the blue support band. Keep
        # that existing structural color zone for every variant consistently.
        ImageDraw.Draw(mask).rectangle((0,55,127,79),fill=0)
    mask.save(HERE/f'final_mask_{key}.png')
    return mask
def compose(key,name,folder):
    clean=Image.open(HERE/f'clean_{key}.png').convert('RGBA');raw=Image.open(EXP/'raw'/f'{name}.png').convert('RGBA')
    assert clean.size==raw.size,(name,clean.size,raw.size)
    mask=final_mask(key);base=clean.copy();identity=Image.new('RGBA',base.size)
    if key in ['lid','shell_end']:
        identity=Image.open(HERE/f'identity_{key}.png').convert('RGBA')
        # Clear only the known functional ID plate, not a material/detail area.
        pixels=np.array(base);pixels[np.array(identity)[:,:,3]>0,:3]=(190,199,194)
        base=Image.fromarray(pixels)
    layer=raw.copy();layer.putalpha(mask)
    final=Image.alpha_composite(Image.alpha_composite(base,layer),identity)
    preserve=np.array(mask)==0
    assert np.array_equal(np.array(final)[preserve],np.array(clean)[preserve])
    out=ASSET/folder;out.mkdir(parents=True,exist_ok=True)
    lay=HERE/'layers'/folder;lay.mkdir(parents=True,exist_ok=True)
    base.save(lay/f'{key}_base.png');layer.save(lay/f'{key}_PixelLab.png');identity.save(lay/f'{key}_functional_ID.png')
    final.save(out/f'{key}.png');final.save(lay/f'{key}_composite.png')
    return {'role':key,'variant':folder,'raw':name,'size':list(final.size),'protected_pixels_exact':True,'changed_vs_clean_pixels':int(np.sum(np.any(np.array(clean)!=np.array(final),axis=2))),'legacy_age_layers_used':[]}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--variants',default='abcd');args=parser.parse_args()
    records=[]
    for key in SHARED:records.append(compose(key,'shared_'+key,'shared'))
    for variant in args.variants:
        for key in EXTERNAL:records.append(compose(key,variant+'_'+key,'variant_'+variant))
    (HERE/'composite_readback.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print('Composed',len(records),'AI surface maps with exact structural/ID protection.')
if __name__=='__main__':main()
