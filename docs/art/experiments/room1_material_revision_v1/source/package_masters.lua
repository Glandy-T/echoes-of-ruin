local root=app.params.root
for _,key in ipairs({'floor','rear','front','left','right'}) do
 local sprite=app.open(root..'/source/layers/'..key..'_base.png')
 sprite.layers[1].name='01_base_palette'
 local names=key=='floor' and {'broad_material','edge_finish','contact_finish'} or
   {'broad_material','trims','edge_deposit','band_contact','structure','diffuser'}
 for index,name in ipairs(names) do
  local layer=sprite:newLayer();layer.name=string.format('%02d_',index+1)..name
  sprite:newCel(layer,1,Image{fromFile=root..'/source/layers/'..key..'_'..name..'.png'},Point(0,0))
 end
 if key~='floor' then
  local layer=sprite:newLayer();layer.name='EMISSION_MASK_HIDDEN'
  sprite:newCel(layer,1,Image{fromFile=root..'/textures/'..key..'_emission.png'},Point(0,0))
  layer.isVisible=false
 end
 sprite:saveAs(root..'/editable/'..key..'_material_revision_v1.aseprite')
 app.command.SaveFileAs{filename=root..'/textures/'..key..'_albedo.png'}
 sprite:close()
end
