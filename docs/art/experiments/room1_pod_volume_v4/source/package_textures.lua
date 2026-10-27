local root=app.params.root or 'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_pod_volume_v4'
local groups={
 lid={'v3_design_pixel_planes','seam_and_recess_aging','coating_contact_chips','sample_id_12_or_placeholder_UI'},
 shell_side={'v3_design_pixel_planes','seam_and_recess_aging','coating_contact_chips','sample_id_12_or_placeholder_UI'},
 shell_end={'v3_design_pixel_planes','seam_and_recess_aging','coating_contact_chips','sample_id_12_or_placeholder_UI'},
 interior={'v3_design_pixel_planes','seam_and_recess_aging','coating_contact_chips','sample_id_12_or_placeholder_UI'},
 mattress={'v3_design_pixel_planes','seam_and_recess_aging','coating_contact_chips','sample_id_12_or_placeholder_UI'},
 display={'v3_design_pixel_planes','seam_and_recess_aging','coating_contact_chips','sample_id_12_or_placeholder_UI'},
 glass={'clear_glass_tint','localized_pixel_reflections'},section={'section_material_planes','edge_retained_film'} }
for _,key in ipairs({'lid','shell_side','shell_end','interior','mattress','glass','display','section'}) do
 local names=groups[key]
 local sprite=app.open(root..'/source/texture_layers/'..key..'__'..names[1]..'.png');sprite.layers[1].name=names[1]
 for i=2,#names do local layer=sprite:newLayer();layer.name=names[i];sprite:newCel(layer,1,Image{fromFile=root..'/source/texture_layers/'..key..'__'..names[i]..'.png'},Point(0,0)) end
 if key~='section' then local layer=sprite:newLayer();layer.name='v3_source_HIDDEN';sprite:newCel(layer,1,Image{fromFile=root..'/source/texture_layers/'..key..'__v3_source_HIDDEN.png'},Point(0,0));layer.isVisible=false end
 sprite:saveAs(root..'/editable/'..key..'_v4.aseprite');app.command.SaveFileAs{filename=root..'/textures/'..key..'.png'};sprite:close()
 local read=app.open(root..'/editable/'..key..'_v4.aseprite');app.command.SaveFileAs{filename=root..'/source/readback/'..key..'.png'};read:close()
end
