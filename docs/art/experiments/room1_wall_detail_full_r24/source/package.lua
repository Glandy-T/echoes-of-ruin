local root=app.params.root
for _,wall in ipairs({'left','right','front','rear'}) do
 local s=app.open(root..'/source/layers/'..wall..'/base_r22.png')
 s.layers[1].name='existing_exact_lamps_and_protected_construction'
 local layer=s:newLayer();layer.name='PixelLab_r23_density_all_material_replacement'
 s:newCel(layer,1,Image{fromFile=root..'/source/layers/'..wall..'/PixelLab_all_new_material.png'},Point(0,0))
 s:saveAs(root..'/editable/wall_'..wall..'_r24.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..wall..'.png'}
 s:close()
end
