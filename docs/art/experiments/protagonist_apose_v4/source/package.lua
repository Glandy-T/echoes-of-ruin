local root = app.params.root
assert(root and #root > 0)
local sprite = app.open(root .. '/raw/front.png')
sprite.layers[1].name = 'PixelLab_original_Pro_Apose'
local guide = sprite:newLayer()
guide.name = 'Approved_v3_at_same_pixel_scale_hidden'
sprite:newCel(guide, 1, Image{fromFile=root .. '/source/apose_GUIDE.png'}, Point(0,0))
guide.isVisible = false
local pose = sprite:newLayer()
pose.name = 'Apose_before_material_edit_hidden'
sprite:newCel(pose, 1, Image{fromFile=root .. '/source/material_GUIDE.png'}, Point(0,0))
pose.isVisible = false
local refine = sprite:newLayer()
refine.name = 'Local_restore_plain_chest_no_false_bust_seam'
-- Registered restoration only: remove the new short transverse shadow where
-- the preceding project-owned A-pose had plain cloth. No new shading design.
local original = Image{fromFile=root .. '/raw/front.png'}
local previous = Image{fromFile=root .. '/source/material_GUIDE.png'}
local restored = Image(128,128,ColorMode.RGB)
restored:clear()
local pc = app.pixelColor
local base = original:getPixel(64,48)
local changed = 0
for y=41,44 do
  for x=56,72 do
    local now = original:getPixel(x,y)
    local before = previous:getPixel(x,y)
    if pc.rgbaR(now)==174 and pc.rgbaG(now)==190 and pc.rgbaB(now)==197
      and pc.rgbaA(now)==255 and pc.rgbaA(before)==255
      and pc.rgbaR(before)>=220 and pc.rgbaG(before)>=220 and pc.rgbaB(before)>=220 then
      restored:drawPixel(x,y,base)
      changed = changed + 1
    end
  end
end
assert(changed > 0 and changed <= 68)
sprite:newCel(refine,1,restored,Point(0,0))
local face = sprite:newLayer()
face.name = 'Future_upper_face_shade_EMPTY_not_applied'
sprite:saveAs(root .. '/editable/front_apose.aseprite')
sprite:saveCopyAs(root .. '/evidence/aseprite_readback.png')
sprite:saveCopyAs(root .. '/front_apose.png')
local record = io.open(root .. '/source/local_refinement.json','w')
record:write('{"method":"Aseprite independent layer; aligned prior plain-cloth region used as restoration mask",' ..
  '"region_inclusive":[56,41,72,44],"changed_pixels":' .. changed ..
  ',"raw_preserved":true,"alpha_unchanged":true,"reason":"Remove unintended transverse chest seam-like shadow; preserve narrowed sleeves and all other artwork"}')
record:close()
sprite:close()
