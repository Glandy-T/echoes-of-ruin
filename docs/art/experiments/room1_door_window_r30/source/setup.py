from pathlib import Path
import json, hashlib

HERE=Path(__file__).resolve().parent; EXP=HERE.parent; ROOT=HERE.parents[4]
OLD=ROOT/'docs/art/experiments/room1_door_material_r29'
for name in ['source','editable','evidence']:(EXP/name).mkdir(parents=True,exist_ok=True)
(ROOT/'assets/art/room1_door_window_r30').mkdir(parents=True,exist_ok=True)
(EXP/'.gitignore').write_text('*.log\n*.err\n*.blend1\n__pycache__/\n',encoding='utf8')

lua="""local root=app.params.root
local s=app.open(root..'/../room1_door_material_r29/editable/door_front_r29.aseprite')
local patch=Image(s.width,s.height,ColorMode.RGB)
patch:clear()
-- Explicit local pixel cleanup, not new material or generated weathering.
-- Match adjacent matte coating; preserve the original 12x7 status aperture.
for y=61,74 do
 for x=45,66 do
  if not (x>=51 and x<=62 and y>=64 and y<=70) then
   local rim=(x>=50 and x<=63 and y>=63 and y<=71)
   patch:drawPixel(x,y,rim and app.pixelColor.rgba(105,130,129,255) or app.pixelColor.rgba(183,192,179,255))
  end
 end
end
local layer=s:newLayer();layer.name='r30_local_remove_white_bezel_keep_1px_dark_recess'
s:newCel(layer,1,patch,Point(0,0))
s:saveAs(root..'/editable/door_front_r30.aseprite')
app.command.SaveFileAs{filename=root..'/../../../..//assets/art/room1_door_window_r30/door_front.png'}
app.command.SaveFileAs{filename=root..'/source/readback_door.png'}
s:close()
"""
# Export path uses the explicit repository path to avoid relative-depth ambiguity.
lua=lua.replace("root..'/../../../..//assets/art/room1_door_window_r30/door_front.png'",repr((ROOT/'assets/art/room1_door_window_r30/door_front.png').as_posix()))
(HERE/'refine.lua').write_text(lua,encoding='utf8')

p=ROOT/'scripts/dev/room1_door_material_r29.gd'
text=p.read_text(encoding='utf8').replace('r29','r30').replace('R29','R30')
text=text.replace('res://scripts/dev/room1_pod_age_full_r28.gd','res://scripts/dev/room1_door_material_r29.gd').replace('room1_door_material_r30','room1_door_window_r30')
text=text.replace('r28/v7','r29').replace("r28's existing","r29's existing").replace('A r28 / v7 门面基线','A r29 白边基线').replace('B r30 PixelLab 门面候选','B r30 认证窗局部精修').replace('Missing r30 PixelLab','Missing r30 refined')
text=text.replace('2 = r30 PixelLab map.','2 = same PixelLab body + local Aseprite bezel cleanup.')
text+='''\nfunc _unhandled_key_input(event: InputEvent) -> void:
\tif review_ui and review_ui.is_modal_open():
\t\treturn
\tif event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_1, KEY_2]:
\t\tset_r30_mode(1 if event.physical_keycode == KEY_1 else 2)
\t\tget_viewport().set_input_as_handled()
\t\treturn
\tsuper._unhandled_key_input(event)
'''
(ROOT/'scripts/dev/room1_door_window_r30.gd').write_text(text,encoding='utf8')
for kind in ['capture','verify']:
 text=(ROOT/f'scripts/dev/{kind}_room1_door_material_r29.gd').read_text(encoding='utf8').replace('r29','r30').replace('R29','R30').replace('room1_door_material_r30','room1_door_window_r30').replace('A_r28_v7','A_r29').replace('B_r30','B_r30')
 (ROOT/f'scripts/dev/{kind}_room1_door_window_r30.gd').write_text(text,encoding='utf8')
for suffix in ['', '_capture','_verify']:
 text=(ROOT/f'scenes/dev/room1_door_material_r29{suffix}.tscn').read_text(encoding='utf8').replace('room1_door_material_r29','room1_door_window_r30').replace('R29','R30')
 if not suffix:text=text.replace('room1_pod_age_full_r28.tscn','room1_door_material_r29.tscn')
 (ROOT/f'scenes/dev/room1_door_window_r30{suffix}.tscn').write_text(text,encoding='utf8')
text=(OLD/'source/blender_material_source.py').read_text(encoding='utf8')
text=text.replace('room1_pod_age_full_r28/room1_pod_age_full_r28.blend','room1_door_material_r29/room1_door_material_r29.blend')
text=text.replace("old='assets/art/room1_integrated_door_pixellab_v7/door_front.png';new='assets/art/room1_door_material_r29/door_front.png'","old='assets/art/room1_door_material_r29/door_front.png';new='assets/art/room1_door_window_r30/door_front.png'")
text=text.replace("scene['r29_notice']","scene['r30_notice']").replace('room1_door_material_r29.blend\'),compress','room1_door_window_r30.blend\'),compress').replace("str(EXP/'room1_door_material_r29.blend')","str(EXP/'room1_door_window_r30.blend')").replace('R29_BLENDER_PASS','R30_BLENDER_PASS')
(HERE/'blender_material_source.py').write_text(text,encoding='utf8')
paths=list(json.loads((OLD/'source/baseline_hashes.json').read_text(encoding='utf8')).keys())
paths+=['assets/art/room1_door_material_r29/door_front.png','docs/art/experiments/room1_door_material_r29/editable/door_front_r29.aseprite']
(HERE/'frozen_inputs.json').write_text(json.dumps({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},indent=2),encoding='utf8')
print('R30_SETUP_READY')
