-- Assemble the r32 layered master from source/layers/*.png and export the
-- runtime door texture.  Run from the repository root:
--   aseprite -b --script-param root=<repo> --script docs/art/experiments/room1_door_powder_r32/source/build_aseprite.lua
local root = app.params.root
local exp = root .. '/docs/art/experiments/room1_door_powder_r32'
local layers = exp .. '/source/layers/'

local s = Sprite(112, 184, ColorMode.RGB)
local function add(name, file)
  local img = Image{ fromFile = layers .. file }
  local layer = s:newLayer()
  layer.name = name
  s:newCel(layer, 1, img, Point(0, 0))
end
add('01_M05-L_powder_coat_native_crop', 'm05l_base.png')
add('02_r30_darker_traces_on_new_base', 'r30_darker_traces.png')
add('03_r30_seal_ring_and_status_aperture', 'r30_structure.png')
s:deleteLayer(s.layers[1]) -- the empty default layer

s:saveAs(exp .. '/editable/door_front_r32.aseprite')
s:flatten()
s:saveCopyAs(root .. '/assets/art/room1_door_powder_r32/door_front.png')
s:saveCopyAs(exp .. '/source/readback_door.png')
s:close()
