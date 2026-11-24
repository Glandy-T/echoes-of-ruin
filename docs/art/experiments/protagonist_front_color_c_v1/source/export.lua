local p=app.params.root
for _,v in ipairs({"A","B"}) do
 local sp=Sprite(128,128,ColorMode.INDEXED)
 local pal=Palette{fromFile=p.."/palette_"..v..".gpl"}
 sp:setPalette(pal)
 sp.transparentColor=0
 local layers={{"Body - PixelLab","body"},{"Gown - PixelLab","gown"}}
 for i,item in ipairs(layers) do
  local lay=i==1 and sp.layers[1] or sp:newLayer()
  lay.name=item[1]
  local ref=Image{fromFile=p.."/"..item[2].."_index.png"}
  local out=Image(128,128,ColorMode.INDEXED)
  for it in ref:pixels() do out:drawPixel(it.x,it.y,app.pixelColor.rgbaR(it())) end
  sp:newCel(lay,1,out,Point(0,0))
 end
 sp:saveAs(p.."/front_"..v..".aseprite")
 sp:saveCopyAs(p.."/front_"..v..".png")
 sp:close()
end
