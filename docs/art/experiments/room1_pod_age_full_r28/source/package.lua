local root=app.params.root
for _,v in ipairs({'a','b','c','d'}) do
 for _,role in ipairs({'lid','shell_side','shell_end'}) do
  if not (v=='d' and role=='shell_end') then
  local stem=root..'/source/layers/variant_'..v..'/'..role
  local s=app.open(stem..'_base.png');s.layers[1].name='original_structure_no_legacy_age'
  local ai=s:newLayer();ai.name=v=='a' and 'approved_r27_PixelLab_A' or 'new_native_PixelLab_wear_'..v
  s:newCel(ai,1,Image{fromFile=stem..'_PixelLab.png'},Point(0,0))
  local id=s:newLayer();id.name='sample_12_functional_identity'
  s:newCel(id,1,Image{fromFile=stem..'_identity.png'},Point(0,0))
  local refine=s:newLayer();refine.name='local_refinement_if_needed'
  s:saveAs(root..'/editable/'..v..'_'..role..'_r28.aseprite')
  app.command.SaveFileAs{filename=root..'/source/readback_'..v..'_'..role..'.png'}
  s:close()
  end
 end
end
