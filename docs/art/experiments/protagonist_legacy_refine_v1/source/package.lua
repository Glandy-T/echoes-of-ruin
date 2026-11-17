local root = app.params.root
assert(root and #root > 0, 'Pass the experiment absolute path as root')
local guide = app.open(root .. '/source/legacy_reference_2x_GUIDE.png')
local guideImage = guide.cels[1].image:clone()
guide:close()
local sprite = app.open(root .. '/raw/front.png')
sprite.layers[1].name = 'PixelLab_original_Pro_front_candidate'
local reference = sprite:newLayer()
reference.name = 'Legacy_identity_2x_GUIDE_hidden'
sprite:newCel(reference, 1, guideImage, Point(0, 0))
reference.isVisible = false
local refine = sprite:newLayer()
refine.name = 'Aseprite_local_refinement_EMPTY'
sprite:saveAs(root .. '/editable/front_candidate.aseprite')
sprite:saveCopyAs(root .. '/evidence/aseprite_readback.png')
sprite:close()
