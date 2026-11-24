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
sp:saveAs(dir.."/back.aseprite")
sp:saveCopyAs(dir.."/back.png")
