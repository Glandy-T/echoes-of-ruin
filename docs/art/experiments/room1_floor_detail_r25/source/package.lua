local root=app.params.root
for _,key in ipairs({'reference','candidate'}) do
 local s=app.open(root..'/source/layers/'..key..'/base_r22.png')
 s.layers[1].name='current_r22_exact_exterior_and_occupied_floor'
 local l=s:newLayer();l.name=key=='reference' and 'r15_original_PixelLab_local_diagnostic' or 'r25_native_PixelLab_local_material'
 s:newCel(l,1,Image{fromFile=root..'/source/layers/'..key..'/material_replacement.png'},Point(0,0))
 s:saveAs(root..'/editable/floor_'..key..'_r25.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..key..'.png'}
 s:close()
end
