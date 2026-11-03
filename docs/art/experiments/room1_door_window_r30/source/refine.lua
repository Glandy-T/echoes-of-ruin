local root=app.params.root
local s=app.open(root..'/../room1_door_material_r29/editable/door_front_r29.aseprite')
local patch=Image(s.width,s.height,ColorMode.RGB)
patch:clear()
-- Explicit local pixel cleanup, not new material or generated weathering.
-- Match adjacent matte coating; preserve the original 12x7 status aperture.
for y=61,74 do
 for x=45,66 do
  if not (x>=51 and x<=62 and y>=64 and y<=70) then
   local rim=(x>=50 and x<=63 and y>=63 and y<=71)
   patch:drawPixel(x,y,rim and app.pixelColor.rgba(105,130,129,255) or app.pixelColor.rgba(183,192,179,255))
  end
 end
end
local layer=s:newLayer();layer.name='r30_local_remove_white_bezel_keep_1px_dark_recess'
s:newCel(layer,1,patch,Point(0,0))
s:saveAs(root..'/editable/door_front_r30.aseprite')
app.command.SaveFileAs{filename='G:/卒業制作/echoes-of-ruin/assets/art/room1_door_window_r30/door_front.png'}
app.command.SaveFileAs{filename=root..'/source/readback_door.png'}
s:close()
