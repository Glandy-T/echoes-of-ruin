local root=app.params.root or 'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_wall_joints_r3'
-- The unchanged r2 master stays alongside this candidate. Use its exact visible
-- PNG as the base here so alpha recompositing cannot shift inherited colours.
local sprite=app.open(root..'/../../../../assets/art/room1_surface_structure_r2/wall_sample.png')
sprite.layers[1].name='R2_exact_visible_base__editable_master_in_r2'
for _,name in ipairs({'joint_bevels','joint_recessed_seals','joint_end_returns'}) do
 local layer=sprite:newLayer();layer.name='R3_'..name
 sprite:newCel(layer,1,Image{fromFile=root..'/source/layers/'..name..'.png'},Point(0,0))
end
sprite:saveAs(root..'/editable/wall_joints_r3.aseprite')
app.command.SaveFileAs{filename=root..'/source/aseprite_visible_readback.png'}
sprite:close()
