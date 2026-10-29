local root = app.params.root
assert(root, 'root parameter required')
local base = app.open(root .. '/source/guide.png')
base.layers[1].name = 'approved_mineral_and_header'
local layer = base:newLayer()
layer.name = 'pixellab_inpaint_v3_material'
base:newCel(layer, 1, Image{fromFile=root .. '/source/pixellab_material_layer.png'}, Point(0,0))
local headerPath = root .. '/source/pixellab_header_layer.png'
if app.fs.isFile(headerPath) then
  local header = base:newLayer()
  header.name = 'pixellab_top_style_match'
  base:newCel(header, 1, Image{fromFile=headerPath}, Point(0,0))
end
base:saveAs(root .. '/editable/door_front_v7.aseprite')
base:close()
local readback = app.open(root .. '/editable/door_front_v7.aseprite')
app.command.SaveFileAs{filename=root .. '/source/aseprite_readback.png'}
app.command.SaveFileAs{filename=root .. '/../../../../assets/art/room1_integrated_door_pixellab_v7/door_front.png'}
readback:close()
