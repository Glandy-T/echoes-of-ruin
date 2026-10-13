-- Editable AI reference, material, trims, local age, diffuser and emission mask.
local root=app.params.root
for _,key in ipairs({'rear','front','left','right'}) do
 local sprite=app.open(root..'/source/layers/'..key..'_body.png')
 sprite.layers[1].name='01_AI_material_palette_and_edge_finish'
 local function layer(name,file,visible)
  local l=sprite:newLayer();l.name=name
  sprite:newCel(l,1,Image{fromFile=root..'/'..file},Point(0,0))
  l.isVisible=visible
 end
 layer('02_AI_native_age_patches_WALL_SPECIFIC','source/layers/'..key..'_material_age.png',true)
 layer('03_continuous_trim_and_metal_protection','source/layers/'..key..'_trims.png',true)
 layer('04_actual_corners_and_old_contact_age','source/layers/'..key..'_localized_age.png',true)
 layer('05_wide_gray_blue_diffuser_albedo','source/layers/'..key..'_diffuser.png',true)
 layer('EMISSION_MASK_HIDDEN_export_separately','textures/'..key..'_emission.png',false)
 layer('UNMODIFIED_AI_MATERIAL_REFERENCE_HIDDEN','source/layers/'..key..'_ai_reference.png',false)
 layer('ORIGINAL_LAYOUT_GUIDE_HIDDEN','source/layers/'..key..'_layout_reference.png',false)
 sprite:saveAs(root..'/editable/'..key..'_wall_pixel_v2.aseprite')
 app.command.SaveFileAs{filename=root..'/textures/'..key..'_albedo.png'}
 sprite:close()
end
