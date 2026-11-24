local dir=app.params.root
local source=Image{fromFile=dir.."/raw/"..app.params.input}
local sp=Sprite(source.width,source.height,ColorMode.RGB)
sp.layers[1].name="PixelLab rear view"
sp:newCel(sp.layers[1],1,source,Point(0,0))
local overlay=Image(source.width,source.height,ColorMode.RGB)
local mappings={}
local function add(from,to)
  local function color(s)
    return app.pixelColor.rgba(tonumber(s:sub(1,2),16),tonumber(s:sub(3,4),16),tonumber(s:sub(5,6),16),255)
  end
  if from and #from==6 then mappings[color(from)]=color(to) end
end
add("e4dcca","E7DFCF")
add("e3dbca","E7DFCF")
add("7d8c88","80908C")
add("bcb4a3","BEB6A7")
for y=26,92 do
  for x=0,source.width-1 do
    local target=mappings[source:getPixel(x,y)]
    if target then overlay:drawPixel(x,y,target) end
  end
end
local l=sp:newLayer()
l.name="B gown palette"
sp:newCel(l,1,overlay,Point(0,0))
-- Screen-left limbs carry the shadow in the mirrored B reference.
local skin=Image(128,128,ColorMode.RGB)
mappings={}
for _,c in ipairs({"e8be99","f1cca8","cca98e","be9d88"}) do add(c,"C5A891") end
for _,c in ipairs({"957c77","a2867e","b39181"}) do add(c,"99807B") end
for y=43,127 do
  local right=(y<=75 and 55) or (y>=87 and 63) or -1
  for x=0,right do
    local target=mappings[source:getPixel(x,y)]
    if target then skin:drawPixel(x,y,target) end
  end
end
local skinLayer=sp:newLayer()
skinLayer.name="B shadow skin - rear arm and leg"
sp:newCel(skinLayer,1,skin,Point(0,0))
sp:saveAs(dir.."/back.aseprite")
sp:saveCopyAs(dir.."/back.png")
