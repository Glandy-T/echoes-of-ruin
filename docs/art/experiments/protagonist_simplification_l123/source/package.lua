local root=app.params.root
assert(root and #root>0)
local sprite=Sprite(256,384,ColorMode.RGB)
local first=true
for row,level in ipairs({'L1','L2','L3'}) do
  for col,view in ipairs({'front','side'}) do
    local name=level .. '_' .. view
    local at=Point((col-1)*128,(row-1)*128)
    local layers={
      {'source/parts/' .. name .. '_base.png',name .. '_light_body',true},
      {'source/parts/' .. name .. '_shade.png',name .. '_dark_planes',true},
      {'silhouette/' .. name .. '.png',name .. '_PURE_BLACK_hidden',false},
      {'source/parts/' .. name .. '_garment_measure_mask.png',name .. '_measure_body_only_hidden',false}
    }
    for _,spec in ipairs(layers) do
      local layer
      if first then layer=sprite.layers[1];first=false else layer=sprite:newLayer() end
      layer.name=spec[2]
      sprite:newCel(layer,1,Image{fromFile=root .. '/' .. spec[1]},at)
      layer.isVisible=spec[3]
    end
  end
end
sprite:saveAs(root .. '/editable/L123_comparison.aseprite')
sprite:saveCopyAs(root .. '/evidence/aseprite_readback.png')
sprite:close()
