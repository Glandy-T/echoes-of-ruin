local root = app.params.root
assert(root and #root > 0)
local sprite = app.open(root .. '/raw/front.png')
sprite.layers[1].name = 'PixelLab_original_Pro_compact_native'
local guides = {
  {'compact_GUIDE.png', 'Compact_GUIDE_resize_only_hidden'},
  {'legacy_identity.png', 'Legacy_identity_ONLY_not_proportions_hidden'}
}
for _, item in ipairs(guides) do
  local layer = sprite:newLayer()
  layer.name = item[2]
  sprite:newCel(layer, 1, Image{fromFile=root .. '/source/' .. item[1]}, Point(0, 0))
  layer.isVisible = false
end
local refine = sprite:newLayer()
refine.name = 'Aseprite_local_refinement_EMPTY'
sprite:saveAs(root .. '/editable/front_candidate.aseprite')
sprite:saveCopyAs(root .. '/evidence/aseprite_readback.png')
sprite:close()
