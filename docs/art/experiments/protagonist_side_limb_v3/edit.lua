local dir=app.params.root
local base=dir.."/../protagonist_side_c_v1/side"
local sp=app.open(base..".aseprite")
local src=Image{fromFile=base..".png"}
local im=src:clone()
local skin={}
for _,hex in ipairs({"E4BE9A","9D847E","897670","977F78","A68C82","C3A186"}) do
  skin[app.pixelColor.rgba(tonumber(hex:sub(1,2),16),tonumber(hex:sub(3,4),16),tonumber(hex:sub(5,6),16),255)]=true
end
-- Keep the trailing elbow contour; move the leading skin edge one pixel inward.
for y=45,67 do
  local right
  for x=56,73 do if skin[src:getPixel(x,y)] then right=x end end
  im:drawPixel(right-1,y,src:getPixel(right,y))
  im:drawPixel(right,y,src:getPixel(right+1,y))
end
-- Preserve the back of both legs and retain the shadow at the shin edge.
for y=88,118 do
  local right
  for x=55,76 do if app.pixelColor.rgbaA(src:getPixel(x,y))>0 then right=x end end
  local trim=(y>=93 and y<=96) and 2 or 1
  im:drawPixel(right-trim,y,src:getPixel(right,y))
  for x=right-trim+1,right do im:drawPixel(x,y,0) end
end
for _,layer in ipairs(sp.layers) do layer.isVisible=false end
local layer=sp:newLayer()
layer.name="Light arm and shin edit"
sp:newCel(layer,1,im,Point(0,0))
sp:saveAs(dir.."/side.aseprite")
sp:saveCopyAs(dir.."/side.png")
