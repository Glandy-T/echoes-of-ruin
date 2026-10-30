local root=app.params.root
for _,key in ipairs({'reference','a','b'}) do
 local s=app.open(root..'/source/layers/'..key..'/base_r22.png')
 s.layers[1].name='r22_exact_outside_sample_and_protected_construction'
 local layer=s:newLayer();layer.name=key=='reference' and 'original_project_r13_PixelLab_reference' or 'new_PixelLab_native_256_material'
 s:newCel(layer,1,Image{fromFile=root..'/source/layers/'..key..'/PixelLab_material.png'},Point(0,0))
 s:saveAs(root..'/editable/wall_rear_'..key..'_r23.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..key..'.png'}
 s:close()
end
