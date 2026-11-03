local root=app.params.root
-- Keep old back as a disabled rollback layer; replace complete repair regions
-- including transparent margins, otherwise front-facing toes would remain below.
local s=app.open(root..'/../protagonist_turnaround_v1/editable/back.aseprite')
for _,layer in ipairs(s.layers) do layer.isVisible=false end
local base=Image{fromFile=root..'/source/back_v1.png'}
local regions={{41,125,65,151},{127,125,154,151},{57,213,92,246},{101,213,138,246}}
for _,r in ipairs(regions) do
 for y=r[2],r[4] do for x=r[1],r[3] do base:drawPixel(x,y,app.pixelColor.rgba(0,0,0,0)) end end
end
local protected=s:newLayer();protected.name='v1_back_protected_hair_gown_body_outside_limb_masks'
s:newCel(protected,1,base,Point(0,0))
local ai=s:newLayer();ai.name='PixelLab_v2_posterior_hands_Achilles_heels'
s:newCel(ai,1,Image{fromFile=root..'/source/layers/PixelLab_rear_hand_heel_repair.png'},Point(0,0))
local refine=s:newLayer();refine.name='Aseprite_local_refinement_empty'
s:saveAs(root..'/editable/back.aseprite')
app.command.SaveFileAs{filename=root..'/source/readback_back.png'}
s:close()
