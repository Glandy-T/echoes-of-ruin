local root=app.params.root
for _,key in ipairs({'floor','wall'}) do
 local file=key=='floor' and 'floor_coherent_material' or 'wall_material_cleaned'
 local sprite=app.open(root..'/source/layers/'..file..'.png')
 sprite.layers[1].name='01_AI_native_coherent_material_palette_aligned'
 local names=key=='floor' and {} or {'wall_structure','wall_edge_finish','wall_diffuser'}
 for i,name in ipairs(names) do
  local layer=sprite:newLayer();layer.name=string.format('%02d_',i+1)..name
  sprite:newCel(layer,1,Image{fromFile=root..'/source/layers/'..name..'.png'},Point(0,0))
 end
 local raw=sprite:newLayer();raw.name='AI_ORIGINAL_REFERENCE_HIDDEN'
 sprite:newCel(raw,1,Image{fromFile=root..'/raw/'..key..'_pro_00.png'},Point(0,0));raw.isVisible=false
 sprite:saveAs(root..'/editable/'..key..'_surface_sample_r1.aseprite')
 sprite:close()
end
