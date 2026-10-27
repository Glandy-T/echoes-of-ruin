local root=app.params.root or 'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_surface_structure_r2'
for _,key in ipairs({'wall','floor'}) do
 local first=key=='wall' and 'wall_coating' or 'floor_material'
 local sprite=app.open(root..'/source/layers/'..first..'.png')
 sprite.layers[1].name='01_PixelLab_material_palette_and_connected_shapes'
 local layers=key=='wall' and {'wall_structure','wall_edge_finish','wall_trial_end_match'} or {'floor_wall_contact'}
 for i,name in ipairs(layers) do
  local layer=sprite:newLayer();layer.name=string.format('%02d_',i+1)..name
  sprite:newCel(layer,1,Image{fromFile=root..'/source/layers/'..name..'.png'},Point(0,0))
 end
 for _,item in ipairs({{'AI_RAW_HIDDEN','raw/'..key..'_pro_00.png'},{'ORIGINAL_PROJECT_GUIDE_HIDDEN','guides/'..key..'_original.png'}}) do
  local layer=sprite:newLayer();layer.name=item[1]
  sprite:newCel(layer,1,Image{fromFile=root..'/'..item[2]},Point(0,0));layer.isVisible=false
 end
 sprite:saveAs(root..'/editable/'..key..'_structure_r2.aseprite')
 sprite:close()
end
