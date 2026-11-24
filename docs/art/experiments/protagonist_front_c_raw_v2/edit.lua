local p=app.params.root
local raw=Image{fromFile=p.."/../protagonist_front_color_c_v1/raw/master.png"}
local function rgb(r,g,b) return app.pixelColor.rgba(r,g,b,255) end
for _,v in ipairs({"A","B"}) do
 local palette={}
 palette[rgb(216,218,213)]=v=="A" and rgb(225,223,215) or rgb(231,223,207)
 palette[rgb(177,181,174)]=v=="A" and rgb(182,181,173) or rgb(190,182,167)
 palette[rgb(139,142,135)]=v=="A" and rgb(144,145,138) or rgb(150,145,135)
 local sp=Sprite(128,128,ColorMode.RGB)
 sp.layers[1].name="PixelLab original"
 sp:newCel(sp.layers[1],1,raw:clone(),Point(0,0))
 local function overlay(name,im)
  local layer=sp:newLayer()
  layer.name=name
  sp:newCel(layer,1,im,Point(0,0))
  return layer
 end
 local warm=Image(128,128);local cool=Image(128,128)
 for y=27,86 do for x=0,127 do
  local c=raw:getPixel(x,y)
  if palette[c] then warm:drawPixel(x,y,palette[c]) end
  if x>=66 and c==rgb(25,36,33) then cool:drawPixel(x,y,rgb(128,144,140)) end
 end end
 overlay("Right gown shadow",cool)
 overlay("Gown palette "..v,warm)
 local f=Image(128,128)
 -- Shorten the outer edge of each eye and extend the jaw into the neck.
 for _,pt in ipairs({{61,17,197,168,145},{68,17,197,168,145},{62,23,197,168,145},{66,24,197,168,145},{64,25,234,193,157},{65,25,197,168,145},{63,31,197,168,145},{64,31,234,193,157},{65,31,234,193,157},{66,31,197,168,145}}) do
  f:drawPixel(pt[1],pt[2],rgb(pt[3],pt[4],pt[5]))
 end
 local face=overlay("Young adult - face and neck 1px study",f)
 sp:saveCopyAs(p.."/"..v.."_adult.png")
 face.isVisible=false
 sp:saveCopyAs(p.."/"..v.."_original.png")
 sp:saveAs(p.."/"..v..".aseprite")
 sp:close()
end
