local root = app.params.root
assert(root, 'root parameter required')
local names = {'baseline_rear','portal_bay_overlay'}
local source = root .. '/source/portal_wall_layers/'
local sprite = app.open(source .. names[1] .. '.png')
sprite.layers[1].name = names[1]
for index = 2, #names do
  local layer = sprite:newLayer()
  layer.name = names[index]
  sprite:newCel(layer, 1, Image{fromFile=source .. names[index] .. '.png'}, Point(0,0))
end
sprite:saveAs(root .. '/editable/wall_rear_portal.aseprite')
sprite:close()
local readback = app.open(root .. '/editable/wall_rear_portal.aseprite')
app.command.SaveFileAs{filename=root .. '/source/wall_portal_readback.png'}
readback:close()
