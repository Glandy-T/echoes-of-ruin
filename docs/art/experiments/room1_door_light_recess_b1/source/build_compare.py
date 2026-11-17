# Build the r18-vs-B comparison crops. Run: python docs/art/experiments/room1_door_light_recess_b1/source/build_compare.py
import sys; sys.path.insert(0, r'G:/卒業制作/.runtime/python-packages')
from PIL import Image
E=r'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_door_light_recess_b1/evidence/'
def pair(a,b,box,s,out):
    ims=[Image.open(E+x).convert('RGB').crop(box) for x in (a,b)]; ims=[i.resize((i.width*s,i.height*s),Image.NEAREST) for i in ims]
    c=Image.new('RGB',(ims[0].width*2+12,ims[0].height),(19,27,28)); c.paste(ims[0],(0,0)); c.paste(ims[1],(ims[0].width+12,0)); c.save(E+out)
pair('game_open_pass_current_r18.png','game_open_pass_b_recess.png',(500,80,780,400),3,'compare_game_r18_b.png')
pair('oblique_open_current_r18.png','oblique_open_b_recess.png',(300,0,1000,720),1,'compare_oblique_r18_b.png')
