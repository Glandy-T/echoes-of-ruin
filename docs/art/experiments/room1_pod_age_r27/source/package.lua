local root=app.params.root
for _,role in ipairs({'lid','shell_side','shell_end'}) do
 local s=app.open(root..'/source/layers/'..role..'_base.png')
 s.layers[1].name='original_structure_target_density_no_legacy_age'
 local ai=s:newLayer();ai.name='PixelLab_native_material_and_age'
 s:newCel(ai,1,Image{fromFile=root..'/source/layers/'..role..'_PixelLab.png'},Point(0,0))
 local id=s:newLayer();id.name='registered_functional_P12_ID'
 s:newCel(id,1,Image{fromFile=root..'/source/layers/'..role..'_identity.png'},Point(0,0))
 local refine=s:newLayer();refine.name='local_refinement_if_needed'
 s:saveAs(root..'/editable/'..role..'_r27.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..role..'.png'}
 s:close()
end
