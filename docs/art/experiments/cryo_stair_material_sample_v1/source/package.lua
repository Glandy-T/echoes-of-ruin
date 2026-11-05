local root=app.params.root
local assets=app.params.assets
for _,name in ipairs({'mineral_a','mineral_b','tread_edge','wall_body'}) do
  local input=name=='mineral_a' and root..'/source/layers/mineral_a_PixelLab_native.png' or assets..'/'..name..'.png'
  local s=app.open(input)
  s.layers[1].name=name=='wall_body' and 'approved_r24_native_body_crop' or 'PixelLab_native_crop_no_paint_edits'
  local refine=s:newLayer()
  refine.name='local_refinement_EMPTY_not_used_v1'
  if name=='mineral_a' then
    refine.name='local_refine_AI_mask_background_7A8B8B_to_7C8380'
    local base=s.cels[1].image
    local overlay=Image(s.width,s.height,ColorMode.RGB)
    local count=0
    for y=0,s.height-1 do
      for x=0,s.width-1 do
        local p=base:getPixel(x,y)
        if app.pixelColor.rgbaR(p)==122 and app.pixelColor.rgbaG(p)==139 and app.pixelColor.rgbaB(p)==139 then
          overlay:putPixel(x,y,app.pixelColor.rgba(124,131,128,255))
          count=count+1
        end
      end
    end
    s:newCel(refine,1,overlay,Point(0,0))
    overlay:saveAs(root..'/source/layers/mineral_a_background_refine.png')
    print('ASEPRITE_LOCAL_BACKGROUND_COLOR_PIXELS '..count)
  end
  s:saveAs(root..'/editable/'..name..'.aseprite')
  app.command.SaveFileAs{filename=assets..'/'..name..'.png'}
  app.command.SaveFileAs{filename=root..'/source/readback_'..name..'.png'}
  s:close()
end
