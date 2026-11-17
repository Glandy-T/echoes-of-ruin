-- Front silhouette only. Hidden original layers are kept for reversible edits.
local root = app.params.root
local sprite = Sprite(128, 128, ColorMode.RGB)
local parts = {
  {"L2 unchanged body and limbs", "source/parts/unchanged_L2.png", true},
  {"Front gown - mild A line", "source/parts/gown_A_line.png", true},
  {"Short hair - rounded crown and loose tips", "source/parts/short_hair_rounded.png", true},
  {"APPROVED L2 original - hidden reference", "source/L2_front_APPROVED.png", false},
  {"Original straight gown - hidden reference", "source/parts/old_gown.png", false},
  {"Original hair - hidden reference", "source/parts/old_hair.png", false}
}
for i, part in ipairs(parts) do
  local layer = i == 1 and sprite.layers[1] or sprite:newLayer()
  layer.name = part[1]
  sprite:newCel(layer, 1, Image{fromFile=root .. "/" .. part[2]}, Point(0, 0))
  layer.isVisible = part[3]
end
sprite:saveAs(root .. "/editable/front_silhouette.aseprite")
sprite:saveCopyAs(root .. "/evidence/aseprite_readback.png")
sprite:close()
