local dir=app.params.root
local old=dir.."/../protagonist_side_c_v1/side"
local sp=app.open(old..".aseprite")
local original=Image{fromFile=old..".png"}
local edited=original:clone()
-- Re-sample a short horizontal span around its existing centre.
local function narrow(y,left,right,width,cloth)
  local dst=left+math.floor((right-left+1-width)/2+0.5)
  for x=left,right do
    local fill=0
    if cloth then
      fill=original:getPixel(x<dst and left-1 or right+1,y)
    end
    edited:drawPixel(x,y,fill)
  end
  for i=0,width-1 do
    local x=left+math.floor(i*(right-left)/(width-1)+0.5)
    edited:drawPixel(dst+i,y,original:getPixel(x,y))
  end
end
local skin={}
for _,hex in ipairs({"E4BE9A","9D847E","897670","977F78","A68C82","C3A186"}) do
  skin[app.pixelColor.rgba(tonumber(hex:sub(1,2),16),tonumber(hex:sub(3,4),16),tonumber(hex:sub(5,6),16),255)]=true
end
for y=45,67 do
  local left,right
  for x=56,73 do
    if skin[original:getPixel(x,y)] then left=left or x; right=x end
  end
  narrow(y,left,right,math.min(5,right-left+1),true)
end
for y=88,118 do
  local left,right
  for x=55,76 do
    if app.pixelColor.rgbaA(original:getPixel(x,y))>0 then left=left or x; right=x end
  end
  local width=6
  if y<=96 then width=7 elseif y>=110 and y<=116 then width=5 elseif y==118 then width=7 end
  narrow(y,left,right,width,false)
end
for _,layer in ipairs(sp.layers) do layer.isVisible=false end
local layer=sp:newLayer()
layer.name="Side - narrowed limbs"
sp:newCel(layer,1,edited,Point(0,0))
sp:saveAs(dir.."/side.aseprite")
sp:saveCopyAs(dir.."/side.png")
