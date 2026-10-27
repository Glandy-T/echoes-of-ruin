"""Project-authored assembly joints on the existing r2 pixel wall, no generation."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[3]
for name in ['source/layers','editable','evidence','survey']:(ROOT/name).mkdir(parents=True,exist_ok=True)
OUT=PROJECT/'assets/art/room1_wall_joints_r3';OUT.mkdir(parents=True,exist_ok=True)
base=Image.open(PROJECT/'assets/art/room1_surface_structure_r2/wall_sample.png').convert('RGBA')
assert base.size==(256,272)
bevel=Image.new('RGBA',base.size,(0,0,0,0));b=ImageDraw.Draw(bevel)
seal=Image.new('RGBA',base.size,(0,0,0,0));s=ImageDraw.Draw(seal)
finish=Image.new('RGBA',base.size,(0,0,0,0));f=ImageDraw.Draw(finish)
# Two joins, 1.6 m apart: broad panels rather than a dense decorative grid.
# They connect existing lamp return and base protection, never cut the diffuser.
for x in [64,192]:
    for offset,color in [(-4,'#E7E7D4'),(-3,'#B8C4B7'),(-2,'#7D9190'),
                         (1,'#78908D'),(2,'#BBC6BA'),(3,'#D8DBCE')]:
        b.line((x+offset,44,x+offset,248),fill=color)
    s.rectangle((x-1,44,x,248),fill='#41575D')
    # Small axial tonal changes remain within the continuous recessed seal.
    s.rectangle((x-1,96,x,108),fill='#4B6064')
    s.rectangle((x-1,199,x,207),fill='#3C535A')
    # Integer-pixel end returns integrate the joint with existing boundaries.
    f.line((x-4,44,x+3,44),fill='#AAB8AE')
    f.line((x-1,44,x,44),fill='#41575D')
    f.line((x-4,248,x+3,248),fill='#A5B4AA')
    f.line((x-1,248,x,248),fill='#41575D')
layers=[('joint_bevels',bevel),('joint_recessed_seals',seal),('joint_end_returns',finish)]
result=base
for name,layer in layers:
    layer.save(ROOT/'source/layers'/f'{name}.png')
    result=Image.alpha_composite(result,layer)
result.convert('RGB').save(OUT/'wall_sample.png')
base.convert('RGB').resize((768,816),Image.Resampling.NEAREST).save(ROOT/'evidence/wall_r2_native_3x.png')
result.convert('RGB').resize((768,816),Image.Resampling.NEAREST).save(ROOT/'evidence/wall_r3_native_3x.png')
(ROOT/'source/design_record.json').write_text(json.dumps({
 'authority':'User explicitly requested more visible assembly seams after rejecting r2 as too conservative.',
 'authorship':'Project-authored exact Aseprite pixel layers, no external image inputs, no new AI generation.',
 'basis':'r2 wall colour map; existing model/UV/lighting retained.',
 'joint_centers_px':[64,192],'joint_spacing_m':1.6,'joint_dark_core_px':2,
 'joint_full_profile_px':8,'density_candidate_texels_m':80,
 'joint_scope_world_y_m':[0.2875,2.85],
 'joint_world_godot_z_m':[-4.0,-5.6],
 'position_rule':'Stop beneath lamp housing and meet base protection; diffuser and its continuous emission untouched.',
 'seam_type':'Painted bevel/shadow/seal in albedo; not real recessed geometry or a new panel engineering standard.',
 'floor':'r2 floor unchanged','new_generation_usage':0,
 'base_wall_sha256':hashlib.sha256((PROJECT/'assets/art/room1_surface_structure_r2/wall_sample.png').read_bytes()).hexdigest()
},indent=2),encoding='utf-8')
print('Two readable assembly seams saved as independent editable pixel layers.')
