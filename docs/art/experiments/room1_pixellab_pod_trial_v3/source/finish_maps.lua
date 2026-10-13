-- PixelLab surfaces remain on their own untouched source layers.
-- Exact integer-pixel labels are authored here, not AI-generated typography.
-- Command line script parameters are unavailable in this Aseprite build's
-- batch mode.  Keep the explicit parameter when supplied and use this v3
-- directory as the local reproducible fallback.
local root=app.params.root or 'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_pixellab_pod_trial_v3'
local glyphs={
  ['0']={'111','101','101','101','111'},
  ['1']={'010','110','010','010','111'},
  ['U']={'101','101','101','101','111'},
  ['N']={'101','111','111','111','101'},
  ['I']={'111','010','010','010','111'},
  ['T']={'111','010','010','010','010'},
  ['A']={'010','101','111','101','101'},
  ['E']={'111','100','110','100','111'},
  ['M']={'101','111','111','101','101'},
  ['S']={'111','100','111','001','111'},
  ['Y']={'101','101','010','010','010'},
  [':']={'000','010','000','010','000'},
  ['.']={'000','000','000','000','010'},
  ['-']={'000','000','111','000','000'},
  [' ']={'000','000','000','000','000'},
}
local ink=Color{r=37,g=57,b=67,a=255}
local light=Color{r=231,g=231,b=212,a=255}
local label=Color{r=193,g=200,b=188,a=255}
local function rect(img,x,y,w,h,c)
  for yy=y,y+h-1 do for xx=x,x+w-1 do img:drawPixel(xx,yy,c) end end
end
local function text(img,x,y,word,c,scale)
  scale=scale or 1
  for char in word:gmatch('.') do
    local g=glyphs[char] or glyphs[' ']
    for yy=1,5 do for xx=1,3 do
      if g[yy]:sub(xx,xx)=='1' then rect(img,x+(xx-1)*scale,y+(yy-1)*scale,scale,scale,c) end
    end end
    x=x+4*scale
  end
end
for _,key in ipairs({'lid','shell_side','shell_end','interior','mattress','glass','display'}) do
  local file=root..'/textures/'..key..'.png'
  local primary=key=='lid' or key=='shell_side' or key=='shell_end'
  local input=primary and (root..'/raw/'..key..'_pro.png') or (root..'/source/auxiliary/'..key..'.png')
  local sprite=app.open(input)
  sprite.layers[1].name=(key=='lid' or key=='shell_side' or key=='shell_end')
    and 'PixelLab_Pro_raw_surface' or 'Project_authored_pixel_surface'
  local labels=sprite:newLayer()
  labels.name='Exact_pixel_finish_v3_side_ID_removed_screen_layout'
  local overlay=Image(sprite.width,sprite.height,ColorMode.RGB)
  if key=='lid' then
    rect(overlay,47,197,32,12,label)
    text(overlay,49,199,'UNIT 01',ink)
    for i=0,25,3 do rect(overlay,49+i,207,i%2+1,2,ink) end
  elseif key=='shell_side' then
    -- v3: the same map is read from both long sides.  Do not repeat an
    -- arbitrary UNIT 01 marking on both boarding faces.
  elseif key=='shell_end' then
    text(overlay,58,38,'01',ink,2)
  elseif key=='display' then
    -- No protagonist identity or live biomedical state has been confirmed.
    -- Keep this as a readable UI layout: a blank name field, neutral system
    -- rows and static bars rather than invented personal data.
    rect(overlay,6,4,116,40,Color{r=24,g=43,b=53,a=255})
    rect(overlay,8,6,112,1,Color{r=101,g=166,b=166,a=255})
    text(overlay,10,10,'NAME: ----',light)
    rect(overlay,10,18,34,2,Color{r=65,g=87,b=99,a=255})
    rect(overlay,46,18,62,2,Color{r=101,g=166,b=166,a=255})
    text(overlay,10,24,'SYS: ----',Color{r=125,g=146,b=152,a=255})
    rect(overlay,10,32,98,3,Color{r=65,g=87,b=99,a=255})
    rect(overlay,10,32,68,3,Color{r=66,g=124,b=132,a=255})
    rect(overlay,10,38,98,2,Color{r=65,g=87,b=99,a=255})
    rect(overlay,10,38,46,2,Color{r=101,g=166,b=166,a=255})
  end
  sprite:newCel(labels,1,overlay,Point(0,0))
  if key=='lid' or key=='shell_side' or key=='shell_end' then
    local guide=sprite:newLayer()
    guide.name='Original_layout_guide_HIDDEN'
    sprite:newCel(guide,1,Image{fromFile=root..'/guides/'..key..'_layout.png'},Point(0,0))
    guide.isVisible=false
  end
  sprite:saveAs(root..'/editable/'..key..'_v3.aseprite')
  -- Composite export preserves the original source layer and exact label layer.
  app.command.SaveFileAs{filename=file}
  sprite:close()
end
