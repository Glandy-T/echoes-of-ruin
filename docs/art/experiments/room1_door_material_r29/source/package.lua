local root=app.params.root
local s=app.open(root..'/source/layers/protected_structure_clean_base.png')
s.layers[1].name='clean_flat_composite_and_exact_original_seal_status'
local ai=s:newLayer();ai.name='PixelLab_native_matte_coating_and_age'
s:newCel(ai,1,Image{fromFile=root..'/source/layers/PixelLab_matte_composite_age.png'},Point(0,0))
local refine=s:newLayer();refine.name='local_refinement_if_needed'
s:saveAs(root..'/editable/door_front_r29.aseprite')
app.command.SaveFileAs{filename=root..'/source/readback_door.png'}
s:close()
