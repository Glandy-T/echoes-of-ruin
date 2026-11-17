local root=app.params.root
local sprite=Sprite(128,128,ColorMode.RGB)
local layers={
  {"LIGHT - locked silhouette", "source/parts/base_light.png", true},
  {"DARK - broad form planes", "source/parts/shadow_dark.png", true},
  {"APPROVED outline - hidden reference", "source/APPROVED_front_silhouette.png", false}
}
for i,part in ipairs(layers) do
  local layer=i==1 and sprite.layers[1] or sprite:newLayer()
  layer.name=part[1]
  sprite:newCel(layer,1,Image{fromFile=root..'/'..part[2]},Point(0,0))
  layer.isVisible=part[3]
end
sprite:saveAs(root..'/editable/front_twotone.aseprite')
sprite:saveCopyAs(root..'/evidence/aseprite_readback.png')
sprite:close()
