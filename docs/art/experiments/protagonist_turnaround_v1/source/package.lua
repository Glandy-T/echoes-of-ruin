local root=app.params.root
for _,name in ipairs({'side','back'}) do
 local s=app.open(root..'/raw/'..name..'.png')
 s.layers[1].name='PixelLab_original_'..name..'_from_approved_front_v2'
 local layer=s:newLayer();layer.name='Aseprite_local_refinement_empty'
 s:saveAs(root..'/editable/'..name..'.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..name..'.png'}
 s:close()
end
