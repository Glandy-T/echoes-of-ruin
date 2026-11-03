local root=app.params.root
local s=app.open(root..'/raw/front.png')
s.layers[1].name='PixelLab_original_front_design_v1'
local refinement=s:newLayer()
refinement.name='Aseprite_local_refinement_empty'
s:saveAs(root..'/editable/front_design_v1.aseprite')
app.command.SaveFileAs{filename=root..'/source/readback_front.png'}
s:close()
