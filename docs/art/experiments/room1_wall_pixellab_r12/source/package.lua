local root=app.params.root
for _,wall in ipairs({'left','right','front','rear'}) do
  local s=app.open(root..'/source/clean_'..wall..'.png')
  s.layers[1].name='clean_construction_NO_LEGACY_AGE'
  local layer=s:newLayer();layer.name='PixelLab_new_material'
  s:newCel(layer,1,Image{fromFile=root..'/source/'..wall..'_pixellab_layer.png'},Point(0,0))
  s:saveAs(root..'/editable/wall_'..wall..'_r12.aseprite');s:close()
  local r=app.open(root..'/editable/wall_'..wall..'_r12.aseprite')
  app.command.SaveFileAs{filename=root..'/source/readback_'..wall..'.png'}
  app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_wall_pixellab_r12/wall_'..wall..'.png'}
  r:close()
end
