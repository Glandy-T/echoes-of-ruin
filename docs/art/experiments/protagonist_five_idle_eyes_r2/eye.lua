local dir=app.params.root
local shade=Color{r=49,g=59,b=58}
local soft=Color{r=69,g=78,b=72}
local fold=Color{r=153,g=128,b=123}
local edits={
  ["45"]={{56,17,fold},{57,18,shade},{58,18,soft},{61,17,fold},{62,18,shade},{63,18,shade},{64,18,soft}},
  ["90"]={{57,15,fold},{58,15,soft},{59,15,shade},{60,15,soft},{57,16,fold},{58,16,shade},{59,16,shade},{60,16,soft},{59,17,soft}}
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
