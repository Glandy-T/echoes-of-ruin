local root=app.params.root
for _,name in ipairs({'wall_left','pod_lid','pod_shell_side','pod_shell_end'}) do
 local s=app.open(root..'/source/layers/'..name..'_base.png')
 s.layers[1].name='approved_base_only_outside_edit_mask'
 local layer=s:newLayer();layer.name='PixelLab_2x_nearest_material_clusters'
 s:newCel(layer,1,Image{fromFile=root..'/source/layers/'..name..'_PixelLab.png'},Point(0,0))
 s:saveAs(root..'/editable/'..name..'_r20.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..name..'.png'}
 s:close()
end
