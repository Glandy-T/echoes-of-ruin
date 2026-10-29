local root = app.params.root
assert(root, 'root parameter required')
local names = {'mineral_panel','upper_gasket_deposit','seal_and_status','directional_contact_wear'}
local source = root .. '/source/layers/'
local sprite = app.open(source .. names[1] .. '.png')
sprite.layers[1].name = names[1]
for index = 2, #names do
  local layer = sprite:newLayer()
  layer.name = names[index]
  sprite:newCel(layer, 1, Image{fromFile=source .. names[index] .. '.png'}, Point(0,0))
end
sprite:saveAs(root .. '/editable/door_front_v6.aseprite')
sprite:close()
local readback = app.open(root .. '/editable/door_front_v6.aseprite')
app.command.SaveFileAs{filename=root .. '/source/aseprite_readback.png'}
app.command.SaveFileAs{filename=root .. '/../../../../assets/art/room1_integrated_door_finish_v6/door_front.png'}
readback:close()
