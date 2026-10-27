-- Packages the deterministic source layers as editable Aseprite masters and
-- exports their visible compositing to the runtime wall PNGs.
local root=app.params.root or 'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_surface_full_r5'
local names={'left','right','front','rear'}
local layers={'quiet_mineral_plane','structure','joints','top_deposit','lower_accumulation','joint_seal_film','base_contact'}
for _,name in ipairs(names) do
  local sprite=app.open(root..'/source/wall_layers/'..name..'_base.png')
  sprite.layers[1].name='00_base_ceramic_composite'
  for _,layername in ipairs(layers) do
    local layer=sprite:newLayer()
    layer.name=layername
    sprite:newCel(layer,1,Image{fromFile=root..'/source/wall_layers/'..name..'_'..layername..'.png'},Point(0,0))
  end
  sprite:saveAs(root..'/editable/wall_'..name..'.aseprite')
  -- This visible Aseprite export is the runtime asset; no separate flattening.
  app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_surface_full_r5/wall_'..name..'.png'}
  sprite:close()
end
