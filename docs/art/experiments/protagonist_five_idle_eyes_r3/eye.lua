local dir=app.params.root
local shade=Color{r=49,g=59,b=58}
local soft=Color{r=69,g=78,b=72}
local fold=Color{r=153,g=128,b=123}
local corner=Color{r=111,g=99,b=93}
local edits={
  ["45"]={{56,17,soft},{58,17,corner},{57,18,fold},{61,17,soft},{62,17,shade},{63,17,shade},{64,17,corner},{62,18,corner},{63,18,fold}},
  ["90"]={{56,15,fold},{57,15,corner},{58,15,shade},{59,15,shade},{60,15,soft},{61,15,corner},{57,16,fold},{58,16,corner},{59,16,fold}}
}
for angle,points in pairs(edits) do
  local s=app.open(dir.."/../protagonist_five_idle_r1/final_"..angle..".aseprite")
  local layer=s:newLayer()
  layer.name="Lowered eyelid - B palette"
  local eye=Image(128,128,ColorMode.RGB)
  for _,v in ipairs(points) do eye:drawPixel(v[1],v[2],v[3]) end
  s:newCel(layer,1,eye,Point(0,0))
  s:saveAs(dir.."/final_"..angle..".aseprite")
  s:saveCopyAs(dir.."/final_"..angle..".png")
end

