local root = app.params.root
assert(root, 'root parameter required')
local names = {'mineral_composite_base','seal_and_status_window','edge_and_contact_age'}
local source = root .. '/source/layers/'
local sprite = app.open(source .. names[1] .. '.png')
sprite.layers[1].name = names[1]
for index = 2, #names do
  local layer = sprite:newLayer()
  layer.name = names[index]
  sprite:newCel(layer, 1, Image{fromFile=source .. names[index] .. '.png'}, Point(0,0))
end
sprite:saveAs(root .. '/editable/door_front_v3.aseprite')
sprite:close()
local readback = app.open(root .. '/editable/door_front_v3.aseprite')
app.command.SaveFileAs{filename=root .. '/source/aseprite_readback.png'}
-- Aseprite is authoritative for the final alpha-composited runtime pixels.
-- Pillow and Aseprite round semi-transparent edge wear by one RGB step.
app.command.SaveFileAs{filename=root .. '/../../../../assets/art/room1_integrated_door_v3/door_front.png'}
readback:close()
