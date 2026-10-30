local root=app.params.root
local packages=json.decode(io.open(root..'/source/packages.json','r'):read('*a'))
for _,p in ipairs(packages) do
 local s=app.open(root..'/'..p.base)
 s.layers[1].name='retained_structural_or_occupied_pixels'
 for _,entry in ipairs(p.layers) do
  local layer=s:newLayer();layer.name=entry[1]
  s:newCel(layer,1,Image{fromFile=root..'/'..entry[2]},Point(0,0))
 end
 s:saveAs(root..'/editable/'..p.name..'_r22.aseprite')
 app.command.SaveFileAs{filename=root..'/source/readback_'..p.name..'.png'}
 s:close()
end
