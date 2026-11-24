local root=app.params.root
local angle=app.params.angle
local sprite=app.open(root.."/raw_"..angle..".png")
sprite.layers[1].name="PixelLab original"
local edits=Image(128,128,ColorMode.RGB)
local original=sprite.layers[1].cels[1].image
local dark=app.pixelColor.rgba(153,128,123,255) -- B #99807B
local mid=app.pixelColor.rgba(197,168,145,255) -- B #C5A891
local skin_zones={
  ["0"]={{52,88,60,128},{69,88,77,128}},
  ["45"]={{54,88,62,128},{67,88,75,128}},
  ["90"]={{59,88,69,128}},
  ["135"]={{55,88,65,128},{67,88,77,128}},
  ["180"]={{53,88,62,128},{67,88,76,128}},
}
local leg_pixels=0
for _,zone in ipairs(skin_zones[angle]) do
  for y=zone[2],zone[4]-1 do
    for x=zone[1],zone[3]-1 do
      local pixel=original:getPixel(x,y)
      local r=app.pixelColor.rgbaR(pixel)
      local g=app.pixelColor.rgbaG(pixel)
      local b=app.pixelColor.rgbaB(pixel)
      local a=app.pixelColor.rgbaA(pixel)
      local value=r+g+b
      -- The zones contain only exposed lower legs and feet. Preserve the light
      -- skin plane, while converting only the substantial non-B dark clusters.
      if a==255 and value<470 then
        edits:drawPixel(x,y,value<=430 and dark or mid)
        leg_pixels=leg_pixels+1
      end
    end
  end
end
local crown_pixels=0
if angle=="180" then
  -- Lift only the back view's upper-left crown. The right remains in shadow.
  for _,point in ipairs({{60,5},{61,5},{60,6},{61,6},{58,7},{59,7},{60,7},{61,7},{58,8},{59,8},{60,8},{61,8},{57,9},{58,9},{59,9},{60,9},{56,10},{57,10},{59,10},{60,10},{55,11},{56,11}}) do
    edits:drawPixel(point[1],point[2],app.pixelColor.rgba(69,78,72,255)) -- B #454E48
    crown_pixels=crown_pixels+1
  end
end
print("B skin corrections:",angle,leg_pixels,"crown:",crown_pixels)
local layer=sprite:newLayer()
layer.name="Local pixel corrections"
sprite:newCel(layer,1,edits,Point(0,0))
sprite:saveAs(root.."/final_"..angle..".aseprite")
sprite:saveCopyAs(root.."/final_"..angle..".png")
