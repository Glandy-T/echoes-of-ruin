local root=app.params.root
local s=app.open(root..'/../protagonist_front_v1/editable/front_design_v1.aseprite')
local layer=s:newLayer();layer.name='PixelLab_v2_lighter_skin_minimal_facial_planes'
s:newCel(layer,1,Image{fromFile=root..'/source/layers/PixelLab_face_skin_refinement.png'},Point(0,0))
local refine=s:newLayer();refine.name='Aseprite_remove_remaining_brows_eyes_mouth_keep_simple_nose_plane'
local patch=Image(s.width,s.height,ColorMode.RGB);patch:clear()
local base=app.pixelColor.rgba(230,197,170,255)
local soft=app.pixelColor.rgba(217,182,165,255)
-- Explicit local feature cleanup using colors already in the PixelLab result.
-- These named strokes do not redesign the body, outfit or whole face.
for x=100,104 do patch:drawPixel(x,27,base) end
patch:drawPixel(95,27,base)
for y=28,32 do
 for x=90,94 do patch:drawPixel(x,y,base) end
 for x=101,105 do patch:drawPixel(x,y,base) end
end
for x=95,98 do patch:drawPixel(x,38,base) end
for x=94,100 do patch:drawPixel(x,41,soft) end
patch:drawPixel(99,34,soft);patch:drawPixel(99,35,soft)
s:newCel(refine,1,patch,Point(0,0))
s:saveAs(root..'/editable/front_design_v2.aseprite')
app.command.SaveFileAs{filename=root..'/source/readback_front.png'}
app.command.SaveFileAs{filename=root..'/front_design_v2.png'}
s:close()
