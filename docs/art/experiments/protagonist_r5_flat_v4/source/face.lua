local p=app.params.root
local s=app.open(p..'/source/base.png')
s.layers[1].name='Flat B palette - surface regions'
local layer=s:newLayer()
layer.name='Face - manually placed B pixels'
local im=Image(s.spec)
local function dab(r,g,b,points)
  for _,xy in ipairs(points) do im:drawPixel(xy[1],xy[2],Color{r=r,g=g,b=b,a=255}) end
end
-- Use the aligned temple/eye band of the V2 face island, not the old diagonal island.
dab(180,147,130,{{53,61},{54,61},{55,61},{60,61},{61,61},{62,61}})
dab(69,78,72,{{54,62},{55,62},{60,62},{61,62}})
dab(111,99,93,{{54,63},{61,63}})
dab(197,168,145,{{58,65},{57,67}})
dab(180,147,130,{{58,67}})
s:newCel(layer,1,im,Point(0,0))
s:saveAs(p..'/flat.aseprite')
app.command.SaveFileAs{filename=p..'/skin.png'}
s:close()
