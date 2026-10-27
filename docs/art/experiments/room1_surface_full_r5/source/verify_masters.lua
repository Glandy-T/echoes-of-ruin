local root=app.params.root or 'G:/卒業制作/echoes-of-ruin/docs/art/experiments/room1_surface_full_r5'
local pairs={{'floor_aged_r5','floor_aged'},{'floor_leaks_r5','floor_with_leaks'},{'wall_left','wall_left'},{'wall_right','wall_right'},{'wall_front','wall_front'},{'wall_rear','wall_rear'}}
for _,entry in ipairs(pairs) do
 local sprite=app.open(root..'/editable/'..entry[1]..'.aseprite')
 print(entry[1]..' layers='..#sprite.layers..' size='..sprite.width..'x'..sprite.height)
 app.command.SaveFileAs{filename=root..'/source/readback/'..entry[2]..'.png'}
 sprite:close()
end
