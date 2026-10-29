local root=app.params.root
for _,wall in ipairs({'left','right','front','rear'}) do
 local s=app.open(root..'/source/baseline_'..wall..'.png')
 s.layers[1].name='accepted_r12_wall_variants'
 if wall=='rear' then
  local p=s:newLayer();p.name='PixelLab_completed_door_bay'
  s:newCel(p,1,Image{fromFile=root..'/source/'..wall..'_portal_layer.png'},Point(0,0))
 end
 local l=s:newLayer();l.name='PixelLab_lamp_diffuser_and_gaskets'
 s:newCel(l,1,Image{fromFile=root..'/source/'..wall..'_lamp_layer.png'},Point(0,0))
 s:saveAs(root..'/editable/wall_'..wall..'_r13.aseprite');s:close()
 local r=app.open(root..'/editable/wall_'..wall..'_r13.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..wall..'.png'}
 app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_wall_lamp_r13/wall_'..wall..'.png'}
 r:close()
end
