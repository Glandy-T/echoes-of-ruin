local root=app.params.root
for _,name in ipairs({'wall_left','pod_lid','pod_shell_side','pod_shell_end'}) do
 local sprite=app.open(root..'/source/layers/'..name..'_base.png')
 sprite.layers[1].name='approved_structure_and_outside_sample'
 local layer=sprite:newLayer();layer.name='PixelLab_4x_native_graphic_material'
 sprite:newCel(layer,1,Image{fromFile=root..'/source/layers/'..name..'_PixelLab.png'},Point(0,0))
 sprite:saveAs(root..'/editable/'..name..'_r21.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..name..'.png'}
 sprite:close()
end
