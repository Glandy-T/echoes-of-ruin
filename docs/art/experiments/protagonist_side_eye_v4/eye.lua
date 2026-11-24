local dir=app.params.root
local sp=app.open(dir.."/../protagonist_side_limb_v3/side.aseprite")
local eye=Image(128,128,ColorMode.RGB)
local function pixel(x,y,hex)
  eye:drawPixel(x,y,app.pixelColor.rgba(tonumber(hex:sub(1,2),16),tonumber(hex:sub(3,4),16),tonumber(hex:sub(5,6),16),255))
end
-- Skin and warm lid fold from the side; dark lash and iris from front B.
pixel(70,16,"C3A186")
pixel(71,16,"C3A186")
pixel(69,17,"9D847E")
pixel(70,17,"313B3A")
pixel(71,17,"313B3A")
pixel(71,18,"313B3A")
local layer=sp:newLayer()
layer.name="Relaxed upper lid and dark iris"
sp:newCel(layer,1,eye,Point(0,0))
sp:saveAs(dir.."/side.aseprite")
sp:saveCopyAs(dir.."/side.png")
