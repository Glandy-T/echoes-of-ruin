local root=app.params.root or 'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_wall_age_r4'
local sprite=app.open(root..'/../../../../assets/art/room1_wall_joints_r3/wall_sample.png')
sprite.layers[1].name='R3_exact_visible_base__joint_master_preserved_in_r3'
for _,name in ipairs({'upper_recess_deposit','lower_wall_accumulation','joint_edge_old_film','metal_old_contact'}) do
 local layer=sprite:newLayer();layer.name='R4_'..name
 sprite:newCel(layer,1,Image{fromFile=root..'/source/layers/'..name..'.png'},Point(0,0))
end
sprite:saveAs(root..'/editable/wall_age_r4.aseprite')
app.command.SaveFileAs{filename=root..'/source/aseprite_visible_readback.png'}
-- The Aseprite visible export is canonical, including its integer alpha rounding.
app.command.SaveFileAs{filename=root..'/../../../../assets/art/room1_wall_age_r4/wall_sample.png'}
sprite:close()
