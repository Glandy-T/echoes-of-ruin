local root=app.params.root
local assets=app.params.assets
for _,name in ipairs({'mineral_a','mineral_b','tread_edge','wall_body'}) do
  local s=app.open(assets..'/'..name..'.png')
  s.layers[1].name=name=='wall_body' and 'approved_r24_native_body_crop' or 'PixelLab_native_crop_no_paint_edits'
  local refine=s:newLayer()
  refine.name='local_refinement_EMPTY_not_used_v1'
  s:saveAs(root..'/editable/'..name..'.aseprite')
  app.command.SaveFileAs{filename=root..'/source/readback_'..name..'.png'}
  s:close()
end
