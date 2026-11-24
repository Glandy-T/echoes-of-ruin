local dir=app.params.root
local base=dir.."/../protagonist_side_eye_v4/side.aseprite"
for version=1,2 do
  local sprite=app.open(base)
  local patch=Image(128,128,ColorMode.RGB)
  local function pixel(x,y,hex)
    patch:drawPixel(x,y,app.pixelColor.rgba(tonumber(hex:sub(1,2),16),tonumber(hex:sub(3,4),16),tonumber(hex:sub(5,6),16),255))
  end
  pixel(69,17,"E4BE9A")
  pixel(70,17,"9D847E")
  pixel(69,18,"9D847E")
  pixel(70,18,"313B3A")
  pixel(71,18,"E4BE9A")
  if version==2 then
    for x=70,72 do pixel(x,16,"E4BE9A") end
  end
  local layer=sprite:newLayer()
  layer.name=version==1 and "Drooping lid and centered pupil" or "Drooping lid, centered pupil and softened brow"
  sprite:newCel(layer,1,patch,Point(0,0))
  local path=dir.."/variant_"..version
  sprite:saveAs(path..".aseprite")
  sprite:saveCopyAs(path..".png")
  sprite:close()
end
