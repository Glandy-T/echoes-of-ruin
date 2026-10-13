local root=app.params.root
for _,key in ipairs({'A','B'}) do
 local sprite=app.open(root..'/source/layers/common_material.png')
 sprite.layers[1].name='01_AI_matte_material_cleaned_shared'
 local function layer(name,file,visible)
  local l=sprite:newLayer();l.name=name
  sprite:newCel(l,1,Image{fromFile=root..'/'..file},Point(0,0))
  l.isVisible=visible
 end
 layer('02_B_color_zoning_hide_for_uniform','source/layers/B_tonal_color_finish.png',key=='B')
 layer('03_actual_wall_foot_and_flush_threshold','source/layers/common_edge_finish.png',true)
 layer('04_actual_corner_and_faint_contact_finish','source/layers/common_localized_contact.png',true)
 layer('AI_RAW_400px_REFERENCE_HIDDEN','source/layers/AI_RAW_REFERENCE_HIDDEN.png',false)
 local file=key=='A' and 'floor_A_uniform_v1.aseprite' or 'floor_B_tonal_zones_v1.aseprite'
 sprite:saveAs(root..'/editable/'..file)
 app.command.SaveFileAs{filename=root..'/textures/floor_'..key..'_albedo.png'}
 sprite:close()
end
